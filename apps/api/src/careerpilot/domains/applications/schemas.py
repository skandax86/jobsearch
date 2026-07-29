"""Application tracking schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

ApplicationStatus = Literal[
    "interested",
    "tailored",
    "applied",
    "interview",
    "rejected",
    "draft",
    "cancelled",
]


class ApplicationCreate(BaseModel):
    job_posting_id: uuid.UUID
    status: ApplicationStatus = "interested"
    idempotency_key: str | None = Field(default=None, max_length=128)


class ApplicationStatusUpdate(BaseModel):
    status: ApplicationStatus
    reason: str | None = Field(default=None, max_length=500)


class ApplicationPublic(BaseModel):
    id: uuid.UUID
    job_posting_id: uuid.UUID
    status: str
    title: str | None = None
    company: str | None = None
    url: str | None = None
    idempotency_key: str
    updated_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}
