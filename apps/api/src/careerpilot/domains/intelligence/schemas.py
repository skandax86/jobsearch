"""Job matching API schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from careerpilot.domains.jobs.schemas import JobPublic


class RunMatchingRequest(BaseModel):
    resume_id: uuid.UUID | None = None
    limit: int = Field(default=50, ge=1, le=100)
    min_score: float = Field(default=0.0, ge=0.0, le=1.0)


class MatchPublic(BaseModel):
    id: uuid.UUID
    score: float
    confidence: float | None = None
    explanation: dict[str, Any] | None = None
    features: dict[str, Any] | None = None
    model_version: str
    resume_version_id: uuid.UUID | None = None
    job_posting_id: uuid.UUID
    job: JobPublic | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MatchListData(BaseModel):
    items: list[MatchPublic]
    total: int


class RunMatchingData(BaseModel):
    resume_id: uuid.UUID
    resume_version_id: uuid.UUID
    model_version: str
    scored: int
    matched: int
    items: list[MatchPublic]


class ApiResponse(BaseModel):
    data: object | None = None
    metadata: dict = Field(default_factory=dict)
    errors: list = Field(default_factory=list)
