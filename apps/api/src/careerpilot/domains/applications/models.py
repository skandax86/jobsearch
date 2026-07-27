"""Application and Interview domain models."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from careerpilot.db.base import Base, CreatedAtMixin, TimestampMixin, UUIDPrimaryKeyMixin


class ApplicationPackage(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "application_packages"

    job_snapshot_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("job_snapshots.id", ondelete="SET NULL"),
    )
    resume_render_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("resume_renders.id", ondelete="SET NULL"),
    )
    job_snapshot: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    cover_letter: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    answers: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    evidence: Mapped[dict[str, Any] | None] = mapped_column(JSONB)


class Application(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "applications"

    candidate_profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("candidate_profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    job_posting_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("job_postings.id", ondelete="CASCADE"),
        nullable=False,
    )
    application_package_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("application_packages.id", ondelete="SET NULL"),
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False, server_default="draft")
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False)

    package: Mapped[ApplicationPackage | None] = relationship()
    attempts: Mapped[list[ApplicationAttempt]] = relationship(back_populates="application")
    status_history: Mapped[list[ApplicationStatusHistory]] = relationship(
        back_populates="application"
    )
    interviews: Mapped[list[Interview]] = relationship(back_populates="application")

    __table_args__ = (
        UniqueConstraint("idempotency_key", name="uq_applications_idempotency_key"),
        Index("ix_applications_candidate_status", "candidate_profile_id", "status"),
        Index("ix_applications_job_posting_id", "job_posting_id"),
    )


class ApplicationAttempt(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "application_attempts"

    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("applications.id", ondelete="CASCADE"),
        nullable=False,
    )
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    provider_confirmation: Mapped[str | None] = mapped_column(String(512))
    evidence: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    error: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    application: Mapped[Application] = relationship(back_populates="attempts")

    __table_args__ = (
        UniqueConstraint(
            "application_id",
            "attempt_number",
            name="uq_application_attempts_app_number",
        ),
    )


class ApplicationStatusHistory(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "status_history"

    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("applications.id", ondelete="CASCADE"),
        nullable=False,
    )
    from_status: Mapped[str | None] = mapped_column(String(32))
    to_status: Mapped[str] = mapped_column(String(32), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text)
    actor_type: Mapped[str] = mapped_column(String(32), nullable=False, server_default="system")
    actor_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))

    application: Mapped[Application] = relationship(back_populates="status_history")

    __table_args__ = (
        Index("ix_status_history_application_created", "application_id", "created_at"),
    )


class Interview(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "interviews"

    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("applications.id", ondelete="CASCADE"),
        nullable=False,
    )
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(32), nullable=False, server_default="detected")
    location_or_link: Mapped[str | None] = mapped_column(String(1024))
    preparation: Mapped[dict[str, Any] | None] = mapped_column(JSONB)

    application: Mapped[Application] = relationship(back_populates="interviews")

    __table_args__ = (Index("ix_interviews_application_status", "application_id", "status"),)
