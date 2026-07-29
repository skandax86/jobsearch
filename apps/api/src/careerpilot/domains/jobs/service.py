"""Job discovery service — ingest, normalize, dedupe, search."""

from __future__ import annotations

import hashlib
import json
import re
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from careerpilot.domains.jobs.filters import (
    JobSearchFilters,
    filter_discovered_jobs,
    job_matches_filters,
)
from careerpilot.domains.jobs.models import Company, JobPosting, JobSnapshot, JobSource
from careerpilot.domains.jobs.providers.base import DiscoveredJob
from careerpilot.domains.jobs.providers.demo import fetch_demo_jobs
from careerpilot.domains.jobs.providers.naukri import fetch_naukri_jobs
from careerpilot.domains.jobs.providers.remotive import fetch_remotive_jobs


class JobError(Exception):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)


def normalize_company_name(name: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", " ", name.lower()).strip()
    return re.sub(r"\s+", " ", cleaned)


async def _get_or_create_company(
    db: AsyncSession,
    *,
    name: str,
    website: str | None,
    industry: str | None,
) -> Company:
    normalized = normalize_company_name(name) or "unknown"
    company = await db.scalar(select(Company).where(Company.normalized_name == normalized))
    if company is not None:
        changed = False
        if website and not company.website:
            company.website = website
            changed = True
        if industry and not company.industry:
            company.industry = industry
            changed = True
        if changed:
            await db.flush()
        return company

    company = Company(
        name=name.strip() or "Unknown company",
        normalized_name=normalized,
        website=website,
        industry=industry,
        provenance={"source": "job_discovery"},
    )
    db.add(company)
    await db.flush()
    return company


def _snapshot_payload(job: DiscoveredJob) -> dict[str, Any]:
    return {
        "provider": job.provider,
        "external_id": job.external_id,
        "title": job.title,
        "company_name": job.company_name,
        "description": job.description,
        "location": job.location,
        "remote_type": job.remote_type,
        "canonical_url": job.canonical_url,
        "compensation": job.compensation,
        "requirements": job.requirements,
    }


async def _ingest_one(db: AsyncSession, job: DiscoveredJob) -> tuple[JobPosting, bool]:
    """Returns (posting, created)."""
    existing_source = await db.scalar(
        select(JobSource).where(
            JobSource.provider == job.provider,
            JobSource.external_id == job.external_id,
        )
    )

    company = await _get_or_create_company(
        db,
        name=job.company_name,
        website=job.company_website,
        industry=job.company_industry,
    )
    now = datetime.now(UTC)
    snapshot_body = _snapshot_payload(job)
    checksum = hashlib.sha256(json.dumps(snapshot_body, sort_keys=True).encode("utf-8")).hexdigest()

    if existing_source is not None:
        posting = await db.scalar(
            select(JobPosting)
            .where(JobPosting.id == existing_source.job_posting_id)
            .options(selectinload(JobPosting.company))
        )
        if posting is None:
            raise JobError("orphan_source", "Job source references missing posting.")

        posting.title = job.title
        posting.description = job.description
        posting.location = job.location
        posting.remote_type = job.remote_type
        posting.compensation = job.compensation
        posting.requirements = job.requirements
        posting.canonical_url = job.canonical_url
        posting.posted_at = job.posted_at or posting.posted_at
        posting.status = "normalized"
        posting.company_id = company.id

        existing_source.retrieved_at = now
        existing_source.source_url = job.source_url
        existing_source.raw_payload = job.raw_payload

        db.add(
            JobSnapshot(
                job_posting_id=posting.id,
                snapshot=snapshot_body,
                checksum=checksum,
                captured_at=now,
            )
        )
        await db.flush()
        return posting, False

    posting = JobPosting(
        company_id=company.id,
        title=job.title,
        description=job.description,
        location=job.location,
        remote_type=job.remote_type,
        compensation=job.compensation,
        requirements=job.requirements,
        status="normalized",
        posted_at=job.posted_at or now,
        canonical_url=job.canonical_url,
    )
    db.add(posting)
    await db.flush()

    db.add(
        JobSource(
            job_posting_id=posting.id,
            provider=job.provider,
            external_id=job.external_id,
            source_url=job.source_url,
            retrieved_at=now,
            raw_payload=job.raw_payload,
        )
    )
    db.add(
        JobSnapshot(
            job_posting_id=posting.id,
            snapshot=snapshot_body,
            checksum=checksum,
            captured_at=now,
        )
    )
    await db.flush()
    posting.company = company
    return posting, True


async def discover_jobs(
    db: AsyncSession,
    *,
    filters: JobSearchFilters | None = None,
    query: str | None = None,
    include_demo: bool = True,
    include_remotive: bool = True,
    limit: int = 20,
) -> dict[str, Any]:
    search = filters or JobSearchFilters(
        query=query,
        include_demo=include_demo,
        include_remotive=include_remotive,
        limit=limit,
    )
    provider_query = search.provider_search_query()
    # Over-fetch when structured filters are set so we can narrow client-side.
    fetch_limit = min(100, search.limit * 3) if search.has_structured_filters else search.limit

    discovered: list[DiscoveredJob] = []
    warnings: list[str] = []

    if search.include_remotive:
        remotive = await fetch_remotive_jobs(provider_query, limit=fetch_limit)
        discovered.extend(remotive)

    if search.include_naukri:
        naukri, naukri_err = await fetch_naukri_jobs(
            query=provider_query,
            location=search.location,
            country=search.country,
            skills=search.skills,
            experience_level=search.experience_level,
            min_experience_years=search.min_experience_years,
            limit=fetch_limit,
        )
        if naukri_err:
            warnings.append(naukri_err)
        elif not naukri:
            warnings.append("Naukri returned no jobs for these filters.")
        else:
            warnings.append(f"Naukri fetched {len(naukri)} jobs.")
        discovered.extend(naukri)

    if search.include_demo:
        discovered.extend(fetch_demo_jobs(provider_query))

    # Providers apply a coarse text search; re-apply full filters for location/skills/etc.
    if search.has_structured_filters or search.query:
        discovered = filter_discovered_jobs(discovered, search, apply_query=bool(search.query))

    # Prefer remotive, then naukri, then demo; cap total unique by external key order
    seen: set[tuple[str, str]] = set()
    unique: list[DiscoveredJob] = []
    for job in discovered:
        key = (job.provider, job.external_id)
        if key in seen:
            continue
        seen.add(key)
        unique.append(job)
        if len(unique) >= search.limit:
            break

    created = 0
    updated = 0
    postings: list[JobPosting] = []
    for job in unique:
        posting, was_created = await _ingest_one(db, job)
        postings.append(posting)
        if was_created:
            created += 1
        else:
            updated += 1

    await db.commit()
    # Reload with company
    ids = [p.id for p in postings]
    if not ids:
        return {
            "discovered": 0,
            "created": 0,
            "updated": 0,
            "items": [],
            "warnings": warnings,
        }

    result = await db.scalars(
        select(JobPosting)
        .where(JobPosting.id.in_(ids))
        .options(selectinload(JobPosting.company))
        .order_by(JobPosting.posted_at.desc().nullslast(), JobPosting.created_at.desc())
    )
    items = list(result)
    return {
        "discovered": len(unique),
        "created": created,
        "updated": updated,
        "items": items,
        "warnings": warnings,
    }


async def list_jobs(
    db: AsyncSession,
    *,
    filters: JobSearchFilters | None = None,
    query: str | None = None,
    remote_type: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[JobPosting], int]:
    search = filters or JobSearchFilters(query=query, remote_type=remote_type, limit=limit)
    sql_filters = [JobPosting.status.in_(("discovered", "normalized", "eligible"))]
    if search.query:
        q = f"%{search.query.strip()}%"
        sql_filters.append(
            or_(
                JobPosting.title.ilike(q),
                JobPosting.description.ilike(q),
                JobPosting.location.ilike(q),
            )
        )
    if search.remote_type and search.remote_type.lower() not in {"", "any"}:
        sql_filters.append(JobPosting.remote_type == search.remote_type.lower())
    if search.location:
        sql_filters.append(JobPosting.location.ilike(f"%{search.location.strip()}%"))

    # Pull a wider page when post-filtering skills/country/experience
    needs_post = bool(
        search.country
        or search.skills
        or (search.experience_level and search.experience_level.lower() not in {"", "any"})
        or search.min_experience_years is not None
    )
    fetch_limit = min(500, (offset + limit) * 5) if needs_post else limit
    fetch_offset = 0 if needs_post else offset

    result = await db.scalars(
        select(JobPosting)
        .where(*sql_filters)
        .options(selectinload(JobPosting.company))
        .order_by(JobPosting.posted_at.desc().nullslast(), JobPosting.created_at.desc())
        .offset(fetch_offset)
        .limit(fetch_limit if needs_post else limit)
    )
    rows = list(result)

    if needs_post:
        matched = [
            job
            for job in rows
            if job_matches_filters(
                title=job.title,
                description=job.description,
                location=job.location,
                remote_type=job.remote_type,
                requirements=job.requirements if isinstance(job.requirements, dict) else None,
                filters=search,
                apply_query=False,  # already applied in SQL
            )
        ]
        total = len(matched)
        return matched[offset : offset + limit], total

    total = await db.scalar(select(func.count()).select_from(JobPosting).where(*sql_filters))
    return rows, int(total or 0)


async def get_job(db: AsyncSession, *, job_id: uuid.UUID) -> JobPosting:
    job = await db.scalar(
        select(JobPosting)
        .where(JobPosting.id == job_id)
        .options(selectinload(JobPosting.company), selectinload(JobPosting.sources))
    )
    if job is None:
        raise JobError("not_found", "Job not found.")
    return job


async def ingest_linkedin_job_url(
    db: AsyncSession,
    *,
    url: str,
    description_override: str | None = None,
) -> dict[str, Any]:
    """Fetch a LinkedIn job URL and upsert into the job catalog."""
    from careerpilot.domains.jobs.providers.linkedin_url import (
        LinkedInUrlError,
        fetch_linkedin_job_from_url,
    )

    try:
        discovered = await fetch_linkedin_job_from_url(
            url, description_override=description_override
        )
    except LinkedInUrlError as exc:
        raise JobError(exc.code, exc.message) from exc

    posting, created = await _ingest_one(db, discovered)
    await db.commit()
    job = await get_job(db, job_id=posting.id)
    return {"job": job, "created": created}
