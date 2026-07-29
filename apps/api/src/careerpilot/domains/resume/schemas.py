"""Resume API schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator
from sqlalchemy import inspect as sa_inspect

from careerpilot.domains.resume.schema import normalize_resume_content, resume_origin


class ResumePublic(BaseModel):
    id: uuid.UUID
    title: str | None
    status: str
    origin: Literal["uploaded", "generated"] = "uploaded"
    source_mime_type: str | None
    source_checksum: str | None
    source_object_key: str | None
    active_version_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime
    content: dict[str, Any] | None = None
    parser: str | None = None
    ai_parse_error: str | None = None

    model_config = {"from_attributes": True}


class ResumeListData(BaseModel):
    items: list[ResumePublic]


class SaveResumeRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    content: dict[str, Any]
    parent_resume_id: uuid.UUID | None = None
    job_posting_id: uuid.UUID | None = None

    @field_validator("content")
    @classmethod
    def normalize_content(cls, value: dict[str, Any]) -> dict[str, Any]:
        return normalize_resume_content(value)


class UpdateResumeRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    content: dict[str, Any] | None = None

    @field_validator("content")
    @classmethod
    def normalize_content(cls, value: dict[str, Any] | None) -> dict[str, Any] | None:
        if value is None:
            return None
        return normalize_resume_content(value)


class TailorResumeRequest(BaseModel):
    job_posting_id: uuid.UUID | None = None
    job_url: str | None = Field(default=None, max_length=4000)
    description_override: str | None = Field(default=None, max_length=20000)
    selected_suggestion_ids: list[str] | None = None

    @field_validator("job_url")
    @classmethod
    def canonicalize_job_url(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        from careerpilot.domains.jobs.providers.linkedin_url import (
            LinkedInUrlError,
            canonicalize_linkedin_job_url,
        )

        try:
            return canonicalize_linkedin_job_url(value)
        except LinkedInUrlError as exc:
            raise ValueError(exc.message) from exc


class TailorSuggestion(BaseModel):
    id: str
    section: str
    title: str
    rationale: str
    path: str
    before: Any = None
    after: Any = None
    selected_by_default: bool = True


class TailorResumeData(BaseModel):
    model_version: str
    resume_id: uuid.UUID
    job_posting_id: uuid.UUID
    job_title: str
    job_company: str | None = None
    job_url: str | None = None
    match_preview: dict[str, Any]
    suggestions: list[TailorSuggestion]
    current_content: dict[str, Any]
    proposed_content: dict[str, Any]
    applied_content: dict[str, Any] | None = None


class CoverLetterRequest(BaseModel):
    job_posting_id: uuid.UUID | None = None
    job_url: str | None = Field(default=None, max_length=4000)
    description_override: str | None = Field(default=None, max_length=20000)

    @field_validator("job_url")
    @classmethod
    def canonicalize_job_url(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        from careerpilot.domains.jobs.providers.linkedin_url import (
            LinkedInUrlError,
            canonicalize_linkedin_job_url,
        )

        try:
            return canonicalize_linkedin_job_url(value)
        except LinkedInUrlError as exc:
            raise ValueError(exc.message) from exc


class CoverLetterData(BaseModel):
    model_version: str
    resume_id: uuid.UUID
    job_posting_id: uuid.UUID
    job_title: str
    job_company: str | None = None
    job_url: str | None = None
    tone: str
    recipient: str
    subject: str
    text: str
    highlights: dict[str, Any] = Field(default_factory=dict)


class ApiResponse(BaseModel):
    data: object | None = None
    metadata: dict = Field(default_factory=dict)
    errors: list = Field(default_factory=list)


def resume_to_public(resume: Any, *, include_content: bool = False) -> ResumePublic:
    content = None
    parser = None
    ai_parse_error = None
    version = None
    for item in _loaded_versions(resume):
        if resume.active_version_id and item.id == resume.active_version_id:
            version = item
            break
        if version is None:
            version = item
    if version is not None:
        provenance = version.provenance if isinstance(version.provenance, dict) else {}
        parser = provenance.get("parser")
        ai_parse_error = provenance.get("ai_parse_error")
        if include_content and getattr(version, "content", None) is not None:
            # Avoid lazy-load when content relationship was not eager-loaded.
            try:
                insp = sa_inspect(version)
                content_loaded = "content" not in insp.unloaded
            except Exception:
                content_loaded = False
            if content_loaded and version.content is not None:
                content = normalize_resume_content(version.content.content)

    return ResumePublic(
        id=resume.id,
        title=resume.title,
        status=resume.status,
        origin=resume_origin(resume),  # type: ignore[arg-type]
        source_mime_type=resume.source_mime_type,
        source_checksum=resume.source_checksum,
        source_object_key=resume.source_object_key,
        active_version_id=resume.active_version_id,
        created_at=resume.created_at,
        updated_at=resume.updated_at,
        content=content,
        parser=parser if isinstance(parser, str) else None,
        ai_parse_error=ai_parse_error if isinstance(ai_parse_error, str) else None,
    )


def _loaded_versions(resume: Any) -> list[Any]:
    """Return versions only when the relationship is already loaded (no lazy IO)."""
    try:
        insp = sa_inspect(resume)
        if "versions" in insp.unloaded:
            return []
    except Exception:
        return []
    return list(getattr(resume, "versions", None) or [])

