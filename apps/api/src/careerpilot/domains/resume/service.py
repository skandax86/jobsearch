"""Resume domain service — upload, parse, and read."""

from __future__ import annotations

import hashlib
import json
import logging
import re
import uuid
from pathlib import PurePosixPath
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from careerpilot import storage as object_storage
from careerpilot.config import settings
from careerpilot.db.session import AsyncSessionLocal
from careerpilot.domains.candidate.models import CandidateProfile
from careerpilot.domains.identity.models import User
from careerpilot.domains.resume.models import Resume, ResumeContent, ResumeRender, ResumeVersion
from careerpilot.domains.resume.parser.extract import ExtractionError
from careerpilot.domains.resume.schema import normalize_resume_content, resume_origin
from careerpilot.mcp.storage.server import call_storage_tool

logger = logging.getLogger(__name__)

ALLOWED_MIME_TYPES = {
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "application/msword": "doc",
}

ORIGIN_UPLOADED = "uploaded"
ORIGIN_GENERATED = "generated"
SORT_CREATED = "created_at"
SORT_UPDATED = "updated_at"


async def _put_source_object(*, object_key: str, data: bytes, content_type: str) -> None:
    import base64

    result = await call_storage_tool(
        "put_object",
        object_key=object_key,
        data_b64=base64.b64encode(data).decode("ascii"),
        content_type=content_type,
    )
    if result.status != "SUCCESS":
        # Fall back to direct adapter if MCP wrapper fails unexpectedly.
        logger.warning("storage MCP put_object failed: %s", result.error)
        await object_storage.put_object(
            object_key=object_key, data=data, content_type=content_type
        )


async def _get_source_object(object_key: str) -> bytes:
    import base64

    result = await call_storage_tool("get_object", object_key=object_key)
    if result.status == "SUCCESS":
        return base64.b64decode((result.result or {}).get("data_b64") or "")
    logger.warning("storage MCP get_object failed: %s", result.error)
    return await object_storage.get_object(object_key)


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

    await _put_source_object(object_key=object_key, data=data, content_type=mime)

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


async def list_resumes(
    db: AsyncSession,
    *,
    user: User,
    origin: str | None = None,
    sort: str = SORT_CREATED,
    order: str = "desc",
) -> list[Resume]:
    profile = await _require_profile(db, user)
    sort_col = Resume.updated_at if sort == SORT_UPDATED else Resume.created_at
    stmt = (
        select(Resume)
        .where(Resume.candidate_profile_id == profile.id)
        .options(selectinload(Resume.versions).selectinload(ResumeVersion.content))
    )
    if order == "asc":
        stmt = stmt.order_by(sort_col.asc())
    else:
        stmt = stmt.order_by(sort_col.desc())

    result = await db.scalars(stmt)
    resumes = list(result)
    if origin in (ORIGIN_UPLOADED, ORIGIN_GENERATED):
        resumes = [r for r in resumes if resume_origin(r) == origin]
    return resumes


async def save_generated_resume(
    db: AsyncSession,
    *,
    user: User,
    title: str,
    content: dict[str, Any],
    parent_resume_id: uuid.UUID | None = None,
    job_posting_id: uuid.UUID | None = None,
    provenance: dict[str, Any] | None = None,
) -> Resume:
    """Persist tailored/edited JSON as a new generated resume (same schema as uploads)."""
    profile = await _require_profile(db, user)
    cleaned_title = (title or "").strip()[:255] or "Untitled resume"
    content_json = normalize_resume_content(content)
    content_checksum = hashlib.sha256(
        json.dumps(content_json, sort_keys=True).encode("utf-8")
    ).hexdigest()

    parent_version_id = None
    if parent_resume_id is not None:
        parent = await get_resume(db, user=user, resume_id=parent_resume_id)
        parent_version = _active_version(parent)
        parent_version_id = parent_version.id if parent_version else None

    resume = Resume(
        candidate_profile_id=profile.id,
        title=cleaned_title,
        status="extracted",
        source_object_key=None,
        source_mime_type=None,
        source_checksum=None,
    )
    content_row = ResumeContent(
        schema_version=str(content_json.get("schema_version", "1.1")),
        content=content_json,
        content_checksum=content_checksum,
    )
    db.add(content_row)
    await db.flush()

    version = ResumeVersion(
        resume=resume,
        content_id=content_row.id,
        version_number=1,
        kind="generated",
        status="extracted",
        parent_version_id=parent_version_id,
        job_posting_id=job_posting_id,
        provenance={
            "source": "generated",
            "content_checksum": content_checksum,
            **(provenance or {}),
        },
    )
    db.add(resume)
    await db.flush()
    resume.active_version_id = version.id
    await db.commit()
    return await get_resume(db, user=user, resume_id=resume.id)


def get_profile_resume_content(profile: CandidateProfile) -> dict[str, Any]:
    data = profile.profile_data if isinstance(profile.profile_data, dict) else {}
    resume_blob = data.get("resume") if isinstance(data.get("resume"), dict) else data
    # Prefer nested resume key; fall back to treating profile_data as content if it looks like one.
    if isinstance(data.get("resume"), dict):
        return normalize_resume_content(data["resume"])
    if any(k in data for k in ("contact", "experience", "skills", "education", "summary")):
        return normalize_resume_content(resume_blob)
    # Seed from flat headline/summary columns when profile_data is empty.
    return normalize_resume_content(
        {
            "headline": profile.headline,
            "summary": profile.summary,
            "contact": {"location": profile.location},
            "personal": {"job_title": profile.headline},
        }
    )


async def update_profile_resume_content(
    db: AsyncSession,
    *,
    user: User,
    content: dict[str, Any],
) -> CandidateProfile:
    profile = await _require_profile(db, user)
    normalized = normalize_resume_content(content)
    existing = profile.profile_data if isinstance(profile.profile_data, dict) else {}
    profile.profile_data = {**existing, "resume": normalized}
    profile.headline = normalized.get("headline") or normalized.get("personal", {}).get(
        "job_title"
    )
    profile.summary = normalized.get("summary")
    contact = normalized.get("contact") if isinstance(normalized.get("contact"), dict) else {}
    profile.location = contact.get("location")
    await db.commit()
    await db.refresh(profile)
    return profile


async def update_resume(
    db: AsyncSession,
    *,
    user: User,
    resume_id: uuid.UUID,
    title: str | None = None,
    content: dict[str, Any] | None = None,
) -> Resume:
    resume = await get_resume(db, user=user, resume_id=resume_id)
    if title is not None:
        cleaned = title.strip()[:255]
        if not cleaned:
            raise ResumeError("invalid_title", "Resume name cannot be empty.")
        resume.title = cleaned

    if content is not None:
        content_json = normalize_resume_content(content)
        content_checksum = hashlib.sha256(
            json.dumps(content_json, sort_keys=True).encode("utf-8")
        ).hexdigest()
        content_row = ResumeContent(
            schema_version=str(content_json.get("schema_version", "1.1")),
            content=content_json,
            content_checksum=content_checksum,
        )
        db.add(content_row)
        await db.flush()

        parent = _active_version(resume)
        next_number = (max((v.version_number for v in resume.versions), default=0) + 1)
        version = ResumeVersion(
            resume_id=resume.id,
            content_id=content_row.id,
            version_number=next_number,
            kind="edited",
            status="extracted",
            parent_version_id=parent.id if parent else None,
            provenance={
                "source": "user_edit",
                "content_checksum": content_checksum,
            },
        )
        db.add(version)
        await db.flush()
        resume.active_version_id = version.id
        resume.status = "extracted"

    await db.commit()
    return await get_resume(db, user=user, resume_id=resume.id)


async def delete_resume(db: AsyncSession, *, user: User, resume_id: uuid.UUID) -> None:
    """Delete a resume and dependent rows via SQL to avoid ORM nulling resume_id."""
    resume = await get_resume(db, user=user, resume_id=resume_id)
    object_key = resume.source_object_key
    versions = list(resume.versions)
    version_ids = [version.id for version in versions]
    content_ids = [version.content_id for version in versions if version.content_id is not None]

    # Break circular FK: resumes.active_version_id -> resume_versions.id
    await db.execute(
        Resume.__table__.update()
        .where(Resume.id == resume.id)
        .values(active_version_id=None)
    )

    if version_ids:
        await db.execute(
            delete(ResumeRender).where(ResumeRender.resume_version_id.in_(version_ids))
        )
        await db.execute(
            ResumeVersion.__table__.update()
            .where(ResumeVersion.id.in_(version_ids))
            .values(parent_version_id=None)
        )
        await db.execute(delete(ResumeVersion).where(ResumeVersion.id.in_(version_ids)))

    await db.execute(delete(Resume).where(Resume.id == resume.id))

    if content_ids:
        still_used = set(
            await db.scalars(
                select(ResumeVersion.content_id).where(ResumeVersion.content_id.in_(content_ids))
            )
        )
        orphan_ids = [cid for cid in content_ids if cid not in still_used]
        if orphan_ids:
            await db.execute(delete(ResumeContent).where(ResumeContent.id.in_(orphan_ids)))

    # Prevent ORM flush from re-writing deleted identity-map objects.
    for version in versions:
        content = version.content
        db.expunge(version)
        if content is not None:
            try:
                db.expunge(content)
            except Exception:
                pass
    db.expunge(resume)

    await db.commit()
    if object_key:
        try:
            await object_storage.delete_object(object_key)
        except Exception:
            logger.warning("Failed to delete resume object %s", object_key, exc_info=True)


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
    return normalize_resume_content(version.content.content)


def _active_version(resume: Resume) -> ResumeVersion | None:
    if resume.active_version_id:
        for version in resume.versions:
            if version.id == resume.active_version_id:
                return version
    return resume.versions[0] if resume.versions else None


async def parse_resume(db: AsyncSession, *, resume_id: uuid.UUID) -> Resume:
    """Parse via ACP ResumeParseWorkflow → resume MCP tools."""
    from careerpilot.acp.workflows.resume_parse import start_resume_parse

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

    profile = await db.scalar(
        select(CandidateProfile).where(CandidateProfile.id == resume.candidate_profile_id)
    )
    if profile is None:
        raise ResumeError("profile_missing", "Candidate profile missing for resume.")

    resume.status = "parsing"
    version.status = "parsing"
    await db.commit()

    try:
        data = await _get_source_object(resume.source_object_key)
        workflow, result = await start_resume_parse(
            db,
            user_id=profile.user_id,
            resume_id=resume.id,
            source_bytes=data,
            mime_type=resume.source_mime_type,
            correlation_id=str(resume.id),
        )

        if result.status == "failed":
            message = result.error or "Resume parse workflow failed."
            resume.status = "parse_failed"
            version.status = "failed"
            provenance = dict(version.provenance or {})
            provenance.update(
                {
                    "parse_error": message,
                    "acp_workflow_id": str(workflow.id),
                    "acp_workflow_type": workflow.workflow_type,
                    "acp_tasks": result.tasks,
                    "orchestration": "acp+mcp",
                }
            )
            version.provenance = provenance
            await db.commit()
            raise ResumeError("parse_failed", message)

        output = result.output or {}
        content_json = normalize_resume_content(output.get("content") or {})
        parser_name = str(output.get("parser") or "heuristic_v2")
        parser_error = output.get("parser_error")
        content_checksum = str(
            output.get("content_checksum")
            or hashlib.sha256(
                json.dumps(content_json, sort_keys=True).encode("utf-8")
            ).hexdigest()
        )

        content = ResumeContent(
            schema_version=str(content_json.get("schema_version", "1.1")),
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
                "parser": parser_name,
                "raw_text_chars": output.get("raw_text_chars"),
                "content_checksum": content_checksum,
                "schema": "resume_content_v1.1",
                "acp_workflow_id": str(workflow.id),
                "acp_workflow_type": workflow.workflow_type,
                "acp_status": result.status,
                "acp_tasks": result.tasks,
                "confidence": output.get("confidence"),
                "sections_order": output.get("sections_order"),
                "orchestration": "acp+mcp",
            }
        )
        if parser_error:
            provenance["ai_parse_error"] = parser_error
        version.provenance = provenance

        resume.status = "needs_review" if result.status == "needs_review" else "extracted"
        await db.commit()
        await db.refresh(resume)
        return resume
    except ResumeError:
        raise
    except ExtractionError as exc:
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
