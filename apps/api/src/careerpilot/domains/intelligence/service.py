"""Career intelligence service — job matching."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from careerpilot.domains.candidate.models import CandidateProfile, PreferenceSet
from careerpilot.domains.identity.models import User
from careerpilot.domains.intelligence.models import JobMatch, SkillGap
from careerpilot.domains.intelligence.scoring import MODEL_VERSION, score_resume_against_job
from careerpilot.domains.jobs.models import JobPosting, JobSnapshot
from careerpilot.domains.resume.models import Resume, ResumeVersion


class MatchError(Exception):
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
        raise MatchError("profile_missing", "Candidate profile is required.")
    return profile


def _active_version(resume: Resume) -> ResumeVersion | None:
    if resume.active_version_id:
        for version in resume.versions:
            if version.id == resume.active_version_id:
                return version
    return resume.versions[0] if resume.versions else None


async def _load_resume_for_matching(
    db: AsyncSession,
    *,
    profile: CandidateProfile,
    resume_id: uuid.UUID | None,
) -> tuple[Resume, ResumeVersion, dict[str, Any]]:
    query = (
        select(Resume)
        .where(Resume.candidate_profile_id == profile.id)
        .options(selectinload(Resume.versions).selectinload(ResumeVersion.content))
    )
    if resume_id is not None:
        query = query.where(Resume.id == resume_id)

    resumes = list(await db.scalars(query.order_by(Resume.created_at.desc())))
    if not resumes:
        raise MatchError("resume_missing", "Upload and parse a resume before matching.")

    for resume in resumes:
        version = _active_version(resume)
        if version is None or version.content is None:
            continue
        if resume.status not in {"extracted", "needs_review", "verified"}:
            continue
        return resume, version, version.content.content

    raise MatchError(
        "resume_not_parsed",
        "No parsed resume content available. Parse a resume first.",
    )


async def _preferred_remote(db: AsyncSession, profile_id: uuid.UUID) -> str | None:
    pref = await db.scalar(
        select(PreferenceSet)
        .where(
            PreferenceSet.candidate_profile_id == profile_id,
            PreferenceSet.is_active.is_(True),
        )
        .order_by(PreferenceSet.version.desc())
    )
    return pref.remote_policy if pref else None


async def _latest_snapshot_id(db: AsyncSession, job_id: uuid.UUID) -> uuid.UUID | None:
    return await db.scalar(
        select(JobSnapshot.id)
        .where(JobSnapshot.job_posting_id == job_id)
        .order_by(JobSnapshot.captured_at.desc())
        .limit(1)
    )


async def run_matching(
    db: AsyncSession,
    *,
    user: User,
    resume_id: uuid.UUID | None = None,
    limit: int = 50,
    min_score: float = 0.0,
) -> dict[str, Any]:
    profile = await _require_profile(db, user)
    resume, version, content = await _load_resume_for_matching(
        db, profile=profile, resume_id=resume_id
    )
    preferred_remote = await _preferred_remote(db, profile.id)

    jobs = list(
        await db.scalars(
            select(JobPosting)
            .where(JobPosting.status.in_(("discovered", "normalized", "eligible")))
            .options(selectinload(JobPosting.company))
            .order_by(JobPosting.posted_at.desc().nullslast(), JobPosting.created_at.desc())
            .limit(limit)
        )
    )
    if not jobs:
        raise MatchError(
            "jobs_missing",
            "No jobs to match. Discover jobs first.",
        )

    # Replace prior matches for this resume version against the scored job set.
    job_ids = [job.id for job in jobs]
    await db.execute(
        delete(SkillGap).where(
            SkillGap.candidate_profile_id == profile.id,
            SkillGap.job_posting_id.in_(job_ids),
        )
    )
    await db.execute(
        delete(JobMatch).where(
            JobMatch.candidate_profile_id == profile.id,
            JobMatch.resume_version_id == version.id,
            JobMatch.job_posting_id.in_(job_ids),
        )
    )

    created_matches: list[JobMatch] = []
    for job in jobs:
        result = score_resume_against_job(
            resume_content=content,
            job_title=job.title,
            job_description=job.description,
            job_requirements=job.requirements,
            job_remote_type=job.remote_type,
            preferred_remote=preferred_remote,
        )
        if result.score < min_score:
            continue

        snapshot_id = await _latest_snapshot_id(db, job.id)
        match = JobMatch(
            candidate_profile_id=profile.id,
            job_posting_id=job.id,
            resume_version_id=version.id,
            job_snapshot_id=snapshot_id,
            score=result.score,
            confidence=result.confidence,
            explanation=result.explanation,
            features=result.features,
            model_version=result.model_version,
        )
        db.add(match)
        await db.flush()

        if result.missing_skills:
            db.add(
                SkillGap(
                    candidate_profile_id=profile.id,
                    job_posting_id=job.id,
                    job_match_id=match.id,
                    gaps={
                        "missing_skills": result.missing_skills,
                        "matched_skills": result.explanation.get("matched_skills", []),
                    },
                    model_version=MODEL_VERSION,
                )
            )
        created_matches.append(match)

    await db.commit()

    # Reload with job + company for response
    if not created_matches:
        return {
            "resume_id": resume.id,
            "resume_version_id": version.id,
            "model_version": MODEL_VERSION,
            "scored": len(jobs),
            "matched": 0,
            "items": [],
        }

    match_ids = [m.id for m in created_matches]
    items = await _load_matches_by_ids(db, match_ids)
    items.sort(key=lambda m: m.score, reverse=True)
    return {
        "resume_id": resume.id,
        "resume_version_id": version.id,
        "model_version": MODEL_VERSION,
        "scored": len(jobs),
        "matched": len(items),
        "items": items,
    }


async def _load_matches_by_ids(db: AsyncSession, match_ids: list[uuid.UUID]) -> list[JobMatch]:
    if not match_ids:
        return []
    result = await db.scalars(
        select(JobMatch).where(JobMatch.id.in_(match_ids)).order_by(JobMatch.score.desc())
    )
    matches = list(result)
    # Attach job postings for serialization
    job_ids = [m.job_posting_id for m in matches]
    jobs = {
        j.id: j
        for j in await db.scalars(
            select(JobPosting)
            .where(JobPosting.id.in_(job_ids))
            .options(selectinload(JobPosting.company))
        )
    }
    for match in matches:
        match.job_posting = jobs.get(match.job_posting_id)  # type: ignore[attr-defined]
    return matches


async def list_matches(
    db: AsyncSession,
    *,
    user: User,
    min_score: float = 0.0,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[JobMatch], int]:
    profile = await _require_profile(db, user)
    filters = [
        JobMatch.candidate_profile_id == profile.id,
        JobMatch.score >= min_score,
    ]
    total = await db.scalar(select(func.count()).select_from(JobMatch).where(*filters))
    result = await db.scalars(
        select(JobMatch)
        .where(*filters)
        .order_by(JobMatch.score.desc(), JobMatch.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    matches = list(result)
    job_ids = [m.job_posting_id for m in matches]
    if job_ids:
        jobs = {
            j.id: j
            for j in await db.scalars(
                select(JobPosting)
                .where(JobPosting.id.in_(job_ids))
                .options(selectinload(JobPosting.company))
            )
        }
        for match in matches:
            match.job_posting = jobs.get(match.job_posting_id)  # type: ignore[attr-defined]
    return matches, int(total or 0)


async def get_match(db: AsyncSession, *, user: User, match_id: uuid.UUID) -> JobMatch:
    profile = await _require_profile(db, user)
    match = await db.scalar(
        select(JobMatch).where(
            JobMatch.id == match_id,
            JobMatch.candidate_profile_id == profile.id,
        )
    )
    if match is None:
        raise MatchError("not_found", "Match not found.")
    job = await db.scalar(
        select(JobPosting)
        .where(JobPosting.id == match.job_posting_id)
        .options(selectinload(JobPosting.company))
    )
    match.job_posting = job  # type: ignore[attr-defined]
    return match
