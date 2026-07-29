"""Application tracking service."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from careerpilot.domains.applications.models import Application, ApplicationStatusHistory
from careerpilot.domains.candidate.models import CandidateProfile
from careerpilot.domains.identity.models import User
from careerpilot.domains.jobs.models import Company, JobPosting


class ApplicationError(Exception):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)


async def _require_profile(db: AsyncSession, user: User) -> CandidateProfile:
    profile = user.candidate_profile
    if profile is None:
        profile = await db.scalar(
            select(CandidateProfile).where(CandidateProfile.user_id == user.id)
        )
    if profile is None:
        raise ApplicationError("profile_missing", "Candidate profile is required.")
    return profile


def _serialize(app: Application, job: JobPosting | None = None) -> dict[str, Any]:
    posting = job
    company_name = None
    title = None
    url = None
    if posting is not None:
        title = posting.title
        url = posting.canonical_url
        if posting.company is not None:
            company_name = posting.company.name
    now = datetime.now(UTC)
    return {
        "id": app.id,
        "job_posting_id": app.job_posting_id,
        "status": app.status,
        "title": title,
        "company": company_name,
        "url": url,
        "idempotency_key": app.idempotency_key,
        "updated_at": app.updated_at or now,
        "created_at": app.created_at or now,
    }


async def list_applications(db: AsyncSession, *, user: User) -> list[dict[str, Any]]:
    profile = await _require_profile(db, user)
    rows = list(
        await db.scalars(
            select(Application)
            .where(Application.candidate_profile_id == profile.id)
            .where(Application.status != "cancelled")
            .order_by(Application.updated_at.desc())
        )
    )
    if not rows:
        return []

    job_ids = [r.job_posting_id for r in rows]
    jobs = {
        j.id: j
        for j in await db.scalars(
            select(JobPosting)
            .where(JobPosting.id.in_(job_ids))
            .options(selectinload(JobPosting.company))
        )
    }
    return [_serialize(app, jobs.get(app.job_posting_id)) for app in rows]


async def upsert_application(
    db: AsyncSession,
    *,
    user: User,
    job_posting_id: uuid.UUID,
    status: str = "interested",
    idempotency_key: str | None = None,
) -> dict[str, Any]:
    profile = await _require_profile(db, user)
    job = await db.scalar(
        select(JobPosting)
        .where(JobPosting.id == job_posting_id)
        .options(selectinload(JobPosting.company))
    )
    if job is None:
        raise ApplicationError("job_not_found", "Job posting not found.")

    key = idempotency_key or f"track:{profile.id}:{job_posting_id}"
    existing = await db.scalar(select(Application).where(Application.idempotency_key == key))
    if existing is None:
        existing = await db.scalar(
            select(Application).where(
                Application.candidate_profile_id == profile.id,
                Application.job_posting_id == job_posting_id,
                Application.status != "cancelled",
            )
        )

    if existing is not None:
        if existing.status != status:
            history = ApplicationStatusHistory(
                application_id=existing.id,
                from_status=existing.status,
                to_status=status,
                reason="tracker_upsert",
                actor_type="user",
                actor_id=user.id,
            )
            existing.status = status
            db.add(history)
            await db.flush()
            await db.refresh(existing)
        return _serialize(existing, job)

    app = Application(
        candidate_profile_id=profile.id,
        job_posting_id=job_posting_id,
        status=status,
        idempotency_key=key,
    )
    db.add(app)
    await db.flush()
    db.add(
        ApplicationStatusHistory(
            application_id=app.id,
            from_status=None,
            to_status=status,
            reason="tracker_create",
            actor_type="user",
            actor_id=user.id,
        )
    )
    await db.flush()
    await db.refresh(app)
    return _serialize(app, job)


async def update_application_status(
    db: AsyncSession,
    *,
    user: User,
    application_id: uuid.UUID,
    status: str,
    reason: str | None = None,
) -> dict[str, Any]:
    profile = await _require_profile(db, user)
    app = await db.scalar(
        select(Application).where(
            Application.id == application_id,
            Application.candidate_profile_id == profile.id,
        )
    )
    if app is None:
        raise ApplicationError("not_found", "Application not found.")

    if app.status != status:
        db.add(
            ApplicationStatusHistory(
                application_id=app.id,
                from_status=app.status,
                to_status=status,
                reason=reason or "status_update",
                actor_type="user",
                actor_id=user.id,
            )
        )
        app.status = status
        await db.flush()
        await db.refresh(app)

    job = await db.scalar(
        select(JobPosting)
        .where(JobPosting.id == app.job_posting_id)
        .options(selectinload(JobPosting.company))
    )
    return _serialize(app, job)


async def delete_application(
    db: AsyncSession,
    *,
    user: User,
    application_id: uuid.UUID,
) -> None:
    profile = await _require_profile(db, user)
    app = await db.scalar(
        select(Application).where(
            Application.id == application_id,
            Application.candidate_profile_id == profile.id,
        )
    )
    if app is None:
        raise ApplicationError("not_found", "Application not found.")
    db.add(
        ApplicationStatusHistory(
            application_id=app.id,
            from_status=app.status,
            to_status="cancelled",
            reason="tracker_remove",
            actor_type="user",
            actor_id=user.id,
        )
    )
    app.status = "cancelled"
    await db.flush()


async def ensure_company(db: AsyncSession, name: str) -> Company:
    normalized = name.strip().lower()
    company = await db.scalar(select(Company).where(Company.normalized_name == normalized))
    if company is not None:
        return company
    company = Company(name=name.strip(), normalized_name=normalized)
    db.add(company)
    await db.flush()
    return company
