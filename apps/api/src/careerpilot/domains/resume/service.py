"""Resume domain service — upload, parse, and read."""

from __future__ import annotations

import hashlib
import json
import logging
import re
import uuid
from pathlib import PurePosixPath
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from careerpilot import storage as object_storage
from careerpilot.config import settings
from careerpilot.db.session import AsyncSessionLocal
from careerpilot.domains.candidate.models import CandidateProfile
from careerpilot.domains.identity.models import User
from careerpilot.domains.resume.models import Resume, ResumeContent, ResumeVersion
from careerpilot.domains.resume.parser.extract import ExtractionError, extract_text
from careerpilot.domains.resume.parser.structure import structure_resume_text

logger = logging.getLogger(__name__)

ALLOWED_MIME_TYPES = {
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "application/msword": "doc",
}


class ResumeError(Exception):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)


def _safe_title(filename: str | None) -> str:
    if not filename:
        return "Resume"
    name = PurePosixPath(filename).name.strip()
    name = re.sub(r"[^\w.\- ()]+", "_", name)[:255]
    return name or "Resume"


async def _require_profile(db: AsyncSession, user: User) -> CandidateProfile:
    profile = user.candidate_profile
    if profile is None:
        profile = await db.scalar(
            select(CandidateProfile).where(CandidateProfile.user_id == user.id)
        )
    if profile is None:
        raise ResumeError("profile_missing", "Candidate profile is required before uploading.")
    return profile


async def upload_resume(
    db: AsyncSession,
    *,
    user: User,
    filename: str | None,
    content_type: str | None,
    data: bytes,
) -> Resume:
    if not data:
        raise ResumeError("empty_file", "Uploaded file is empty.")
    if len(data) > settings.resume_max_bytes:
        raise ResumeError(
            "file_too_large",
            f"File exceeds the {settings.resume_max_bytes // (1024 * 1024)}MB limit.",
        )

    mime = (content_type or "").split(";")[0].strip().lower()
    if mime not in ALLOWED_MIME_TYPES:
        raise ResumeError(
            "unsupported_type",
            "Only PDF and Word documents (.pdf, .docx, .doc) are supported.",
        )

    profile = await _require_profile(db, user)
    ext = ALLOWED_MIME_TYPES[mime]
    checksum = hashlib.sha256(data).hexdigest()
    resume_id = uuid.uuid4()
    object_key = f"users/{user.id}/resumes/{resume_id}/source.{ext}"

    await object_storage.put_object(object_key=object_key, data=data, content_type=mime)

    resume = Resume(
        id=resume_id,
        candidate_profile_id=profile.id,
        title=_safe_title(filename),
        status="parsing",
        source_object_key=object_key,
        source_mime_type=mime,
        source_checksum=checksum,
    )
    version = ResumeVersion(
        resume=resume,
        version_number=1,
        kind="source",
        status="parsing",
        provenance={
            "source": "user_upload",
            "filename": filename,
            "checksum_sha256": checksum,
            "mime_type": mime,
        },
    )
    db.add(resume)
    await db.flush()
    resume.active_version_id = version.id
    await db.commit()
    await db.refresh(resume)
    return resume


async def list_resumes(db: AsyncSession, *, user: User) -> list[Resume]:
    profile = await _require_profile(db, user)
    result = await db.scalars(
        select(Resume)
        .where(Resume.candidate_profile_id == profile.id)
        .options(selectinload(Resume.versions).selectinload(ResumeVersion.content))
        .order_by(Resume.created_at.desc())
    )
    return list(result)


async def get_resume(db: AsyncSession, *, user: User, resume_id: uuid.UUID) -> Resume:
    profile = await _require_profile(db, user)
    resume = await db.scalar(
        select(Resume)
        .where(
            Resume.id == resume_id,
            Resume.candidate_profile_id == profile.id,
        )
        .options(
            selectinload(Resume.versions).selectinload(ResumeVersion.content),
        )
    )
    if resume is None:
        raise ResumeError("not_found", "Resume not found.")
    return resume


async def get_resume_content(
    db: AsyncSession, *, user: User, resume_id: uuid.UUID
) -> dict[str, Any] | None:
    resume = await get_resume(db, user=user, resume_id=resume_id)
    version = _active_version(resume)
    if version is None or version.content is None:
        return None
    return version.content.content


def _active_version(resume: Resume) -> ResumeVersion | None:
    if resume.active_version_id:
        for version in resume.versions:
            if version.id == resume.active_version_id:
                return version
    return resume.versions[0] if resume.versions else None


async def parse_resume(db: AsyncSession, *, resume_id: uuid.UUID) -> Resume:
    resume = await db.scalar(
        select(Resume)
        .where(Resume.id == resume_id)
        .options(selectinload(Resume.versions).selectinload(ResumeVersion.content))
    )
    if resume is None:
        raise ResumeError("not_found", "Resume not found.")
    if not resume.source_object_key or not resume.source_mime_type:
        raise ResumeError("missing_source", "Resume has no source file to parse.")

    version = _active_version(resume)
    if version is None:
        raise ResumeError("missing_version", "Resume has no active version.")

    resume.status = "parsing"
    version.status = "parsing"
    await db.commit()

    try:
        data = await object_storage.get_object(resume.source_object_key)
        raw_text = extract_text(data=data, mime_type=resume.source_mime_type)
        content_json = structure_resume_text(raw_text)
        content_checksum = hashlib.sha256(
            json.dumps(content_json, sort_keys=True).encode("utf-8")
        ).hexdigest()

        content = ResumeContent(
            schema_version=str(content_json.get("schema_version", "1.0")),
            content=content_json,
            content_checksum=content_checksum,
        )
        db.add(content)
        await db.flush()

        version.content_id = content.id
        version.status = "extracted"
        provenance = dict(version.provenance or {})
        provenance.update(
            {
                "parser": "heuristic_v1",
                "raw_text_chars": len(raw_text),
                "content_checksum": content_checksum,
            }
        )
        version.provenance = provenance

        # Needs review when almost no structured sections were found.
        has_structure = any(
            content_json.get(key)
            for key in ("experience", "skills", "projects", "education", "summary")
        )
        resume.status = "extracted" if has_structure else "needs_review"
        await db.commit()
        await db.refresh(resume)
        return resume
    except (ExtractionError, ResumeError) as exc:
        message = getattr(exc, "message", str(exc))
        resume.status = "parse_failed"
        version.status = "failed"
        provenance = dict(version.provenance or {})
        provenance["parse_error"] = message
        version.provenance = provenance
        await db.commit()
        raise ResumeError("parse_failed", message) from exc
    except Exception as exc:
        logger.exception("Unexpected resume parse failure for %s", resume_id)
        resume.status = "parse_failed"
        version.status = "failed"
        provenance = dict(version.provenance or {})
        provenance["parse_error"] = "Unexpected parser failure."
        version.provenance = provenance
        await db.commit()
        raise ResumeError("parse_failed", "Unexpected parser failure.") from exc


async def parse_resume_for_user(db: AsyncSession, *, user: User, resume_id: uuid.UUID) -> Resume:
    # Ownership check
    await get_resume(db, user=user, resume_id=resume_id)
    return await parse_resume(db, resume_id=resume_id)


async def parse_resume_job(resume_id: uuid.UUID) -> None:
    """Background entrypoint with its own DB session."""
    async with AsyncSessionLocal() as db:
        try:
            await parse_resume(db, resume_id=resume_id)
        except ResumeError:
            logger.info("Resume parse finished with domain error for %s", resume_id)
        except Exception:
            logger.exception("Resume parse job crashed for %s", resume_id)
