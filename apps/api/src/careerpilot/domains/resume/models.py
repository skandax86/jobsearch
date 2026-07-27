"""Resume domain models."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Boolean,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from careerpilot.db.base import (
    EMBEDDING_DIMENSIONS,
    Base,
    CreatedAtMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)

if TYPE_CHECKING:
    from careerpilot.domains.candidate.models import CandidateProfile
    from careerpilot.domains.jobs.models import JobPosting


class Resume(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "resumes"

    candidate_profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("candidate_profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(32), nullable=False, server_default="uploaded")
    active_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "resume_versions.id",
            ondelete="SET NULL",
            use_alter=True,
            name="fk_resumes_active_version_id",
        ),
    )
    source_object_key: Mapped[str | None] = mapped_column(String(1024))
    source_mime_type: Mapped[str | None] = mapped_column(String(128))
    source_checksum: Mapped[str | None] = mapped_column(String(128))

    candidate_profile: Mapped[CandidateProfile] = relationship(back_populates="resumes")
    versions: Mapped[list[ResumeVersion]] = relationship(
        back_populates="resume",
        foreign_keys="ResumeVersion.resume_id",
    )

    __table_args__ = (
        Index("ix_resumes_candidate_profile_id_status", "candidate_profile_id", "status"),
    )


class ResumeContent(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "resume_contents"

    schema_version: Mapped[str] = mapped_column(String(32), nullable=False)
    content: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    content_checksum: Mapped[str] = mapped_column(String(128), nullable=False)

    versions: Mapped[list[ResumeVersion]] = relationship(back_populates="content")


class ResumeVersion(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "resume_versions"

    resume_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("resumes.id", ondelete="CASCADE"),
        nullable=False,
    )
    content_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("resume_contents.id", ondelete="SET NULL"),
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    kind: Mapped[str] = mapped_column(String(32), nullable=False, server_default="source")
    status: Mapped[str] = mapped_column(String(32), nullable=False, server_default="draft")
    parent_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("resume_versions.id", ondelete="SET NULL"),
    )
    job_posting_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("job_postings.id", ondelete="SET NULL"),
    )
    provenance: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(EMBEDDING_DIMENSIONS))
    embedding_model: Mapped[str | None] = mapped_column(String(128))
    embedding_model_version: Mapped[str | None] = mapped_column(String(64))

    resume: Mapped[Resume] = relationship(
        back_populates="versions",
        foreign_keys=[resume_id],
    )
    content: Mapped[ResumeContent | None] = relationship(back_populates="versions")
    parent_version: Mapped[ResumeVersion | None] = relationship(remote_side="ResumeVersion.id")
    job_posting: Mapped[JobPosting | None] = relationship()
    renders: Mapped[list[ResumeRender]] = relationship(back_populates="resume_version")

    __table_args__ = (
        UniqueConstraint("resume_id", "version_number", name="uq_resume_versions_resume_number"),
        Index("ix_resume_versions_resume_id_status", "resume_id", "status"),
    )


class ResumeTemplate(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "resume_templates"

    name: Mapped[str] = mapped_column(String(128), nullable=False)
    version: Mapped[str] = mapped_column(String(32), nullable=False)
    format: Mapped[str] = mapped_column(String(32), nullable=False)
    definition: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    definition_object_key: Mapped[str | None] = mapped_column(String(1024))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")

    renders: Mapped[list[ResumeRender]] = relationship(back_populates="template")

    __table_args__ = (UniqueConstraint("name", "version", name="uq_resume_templates_name_version"),)


class ResumeRender(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "resume_renders"

    resume_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("resume_versions.id", ondelete="CASCADE"),
        nullable=False,
    )
    template_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("resume_templates.id", ondelete="SET NULL"),
    )
    format: Mapped[str] = mapped_column(String(16), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, server_default="queued")
    object_key: Mapped[str | None] = mapped_column(String(1024))
    checksum: Mapped[str | None] = mapped_column(String(128))
    mime_type: Mapped[str | None] = mapped_column(String(128))
    renderer_version: Mapped[str | None] = mapped_column(String(64))
    template_version: Mapped[str | None] = mapped_column(String(64))
    validation_report: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    page_count: Mapped[int | None] = mapped_column(Integer)
    error: Mapped[str | None] = mapped_column(Text)

    resume_version: Mapped[ResumeVersion] = relationship(back_populates="renders")
    template: Mapped[ResumeTemplate | None] = relationship(back_populates="renders")

    __table_args__ = (Index("ix_resume_renders_version_status", "resume_version_id", "status"),)
