"""Candidate domain models."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from careerpilot.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from careerpilot.domains.identity.models import User
    from careerpilot.domains.resume.models import Resume


class CandidateProfile(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "candidate_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    headline: Mapped[str | None] = mapped_column(String(255))
    summary: Mapped[str | None] = mapped_column(Text)
    location: Mapped[str | None] = mapped_column(String(255))
    work_authorization: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    profile_data: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    preferences_version: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")

    user: Mapped[User] = relationship(back_populates="candidate_profile")
    facts: Mapped[list[CandidateFact]] = relationship(back_populates="candidate_profile")
    preferences: Mapped[list[PreferenceSet]] = relationship(back_populates="candidate_profile")
    automation_policies: Mapped[list[AutomationPolicy]] = relationship(
        back_populates="candidate_profile"
    )
    resumes: Mapped[list[Resume]] = relationship(back_populates="candidate_profile")

    __table_args__ = (UniqueConstraint("user_id", name="uq_candidate_profiles_user_id"),)


class CandidateFact(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "candidate_facts"

    candidate_profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("candidate_profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    fact_type: Mapped[str] = mapped_column(String(64), nullable=False)
    fact_key: Mapped[str] = mapped_column(String(128), nullable=False)
    fact_value: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    source: Mapped[str] = mapped_column(String(32), nullable=False, server_default="user")
    confidence: Mapped[float | None] = mapped_column(Float)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    provenance: Mapped[dict[str, Any] | None] = mapped_column(JSONB)

    candidate_profile: Mapped[CandidateProfile] = relationship(back_populates="facts")

    __table_args__ = (
        Index("ix_candidate_facts_profile_type", "candidate_profile_id", "fact_type"),
    )


class PreferenceSet(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "preferences"

    candidate_profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("candidate_profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    roles: Mapped[list[Any] | dict[str, Any] | None] = mapped_column(JSONB)
    locations: Mapped[list[Any] | dict[str, Any] | None] = mapped_column(JSONB)
    compensation: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    remote_policy: Mapped[str | None] = mapped_column(String(64))
    blocked_companies: Mapped[list[Any] | None] = mapped_column(JSONB)
    other: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")

    candidate_profile: Mapped[CandidateProfile] = relationship(back_populates="preferences")

    __table_args__ = (
        UniqueConstraint(
            "candidate_profile_id",
            "version",
            name="uq_preferences_profile_version",
        ),
        Index("ix_preferences_profile_active", "candidate_profile_id", "is_active"),
    )


class AutomationPolicy(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "automation_policies"

    candidate_profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("candidate_profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    max_daily_applications: Mapped[int | None] = mapped_column(Integer)
    require_approval: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    rules: Mapped[dict[str, Any] | None] = mapped_column(JSONB)

    candidate_profile: Mapped[CandidateProfile] = relationship(back_populates="automation_policies")

    __table_args__ = (
        Index("ix_automation_policies_profile_enabled", "candidate_profile_id", "enabled"),
    )
