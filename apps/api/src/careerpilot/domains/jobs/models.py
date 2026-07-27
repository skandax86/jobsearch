"""Job and Company domain models."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from careerpilot.db.base import (
    EMBEDDING_DIMENSIONS,
    Base,
    CreatedAtMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)


class Company(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "companies"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    normalized_name: Mapped[str] = mapped_column(String(255), nullable=False)
    website: Mapped[str | None] = mapped_column(String(512))
    industry: Mapped[str | None] = mapped_column(String(128))
    enrichment: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    provenance: Mapped[dict[str, Any] | None] = mapped_column(JSONB)

    job_postings: Mapped[list[JobPosting]] = relationship(back_populates="company")

    __table_args__ = (Index("ix_companies_normalized_name", "normalized_name"),)


class JobPosting(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "job_postings"

    company_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="SET NULL"),
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    location: Mapped[str | None] = mapped_column(String(255))
    remote_type: Mapped[str | None] = mapped_column(String(64))
    compensation: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    requirements: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(String(32), nullable=False, server_default="discovered")
    posted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    canonical_url: Mapped[str | None] = mapped_column(String(2048))
    embedding: Mapped[list[float] | None] = mapped_column(Vector(EMBEDDING_DIMENSIONS))
    embedding_model: Mapped[str | None] = mapped_column(String(128))
    embedding_model_version: Mapped[str | None] = mapped_column(String(64))

    company: Mapped[Company | None] = relationship(back_populates="job_postings")
    sources: Mapped[list[JobSource]] = relationship(back_populates="job_posting")
    snapshots: Mapped[list[JobSnapshot]] = relationship(back_populates="job_posting")

    __table_args__ = (
        Index("ix_job_postings_status_posted_at", "status", "posted_at"),
        Index("ix_job_postings_company_id", "company_id"),
    )


class JobSource(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "job_sources"

    job_posting_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("job_postings.id", ondelete="CASCADE"),
        nullable=False,
    )
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(2048))
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    raw_payload_object_key: Mapped[str | None] = mapped_column(String(1024))
    raw_payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB)

    job_posting: Mapped[JobPosting] = relationship(back_populates="sources")

    __table_args__ = (
        UniqueConstraint("provider", "external_id", name="uq_job_sources_provider_external_id"),
        Index("ix_job_sources_job_posting_id", "job_posting_id"),
    )


class JobSnapshot(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "job_snapshots"

    job_posting_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("job_postings.id", ondelete="CASCADE"),
        nullable=False,
    )
    snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    checksum: Mapped[str] = mapped_column(String(128), nullable=False)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    job_posting: Mapped[JobPosting] = relationship(back_populates="snapshots")

    __table_args__ = (Index("ix_job_snapshots_job_posting_id", "job_posting_id"),)
