"""Resume API schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ResumePublic(BaseModel):
    id: uuid.UUID
    title: str | None
    status: str
    source_mime_type: str | None
    source_checksum: str | None
    source_object_key: str | None
    active_version_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime
    content: dict[str, Any] | None = None

    model_config = {"from_attributes": True}


class ResumeListData(BaseModel):
    items: list[ResumePublic]


class ApiResponse(BaseModel):
    data: object | None = None
    metadata: dict = Field(default_factory=dict)
    errors: list = Field(default_factory=list)


def resume_to_public(resume: Any, *, include_content: bool = False) -> ResumePublic:
    content = None
    if include_content and getattr(resume, "versions", None):
        active_id = resume.active_version_id
        version = None
        for item in resume.versions:
            if active_id and item.id == active_id:
                version = item
                break
        if version is None and resume.versions:
            version = resume.versions[0]
        if version is not None and version.content is not None:
            content = version.content.content

    return ResumePublic(
        id=resume.id,
        title=resume.title,
        status=resume.status,
        source_mime_type=resume.source_mime_type,
        source_checksum=resume.source_checksum,
        source_object_key=resume.source_object_key,
        active_version_id=resume.active_version_id,
        created_at=resume.created_at,
        updated_at=resume.updated_at,
        content=content,
    )
