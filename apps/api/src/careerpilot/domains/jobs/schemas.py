"""Job discovery API schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class DiscoverJobsRequest(BaseModel):
    query: str | None = Field(default=None, max_length=200)
    location: str | None = Field(default=None, max_length=200)
    country: str | None = Field(default=None, max_length=100)
    remote_type: str | None = Field(
        default=None,
        description="remote | hybrid | onsite | any",
    )
    skills: list[str] = Field(default_factory=list, max_length=20)
    experience_level: str | None = Field(
        default=None,
        description="junior | mid | senior | any",
    )
    min_experience_years: int | None = Field(default=None, ge=0, le=40)
    include_demo: bool = True
    include_remotive: bool = True
    include_naukri: bool = False
    limit: int = Field(default=20, ge=1, le=50)


class CompanyPublic(BaseModel):
    id: uuid.UUID
    name: str
    website: str | None = None
    industry: str | None = None

    model_config = {"from_attributes": True}


class JobPublic(BaseModel):
    id: uuid.UUID
    title: str
    description: str | None = None
    location: str | None = None
    remote_type: str | None = None
    compensation: dict[str, Any] | None = None
    requirements: dict[str, Any] | None = None
    status: str
    posted_at: datetime | None = None
    canonical_url: str | None = None
    company: CompanyPublic | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class JobListData(BaseModel):
    items: list[JobPublic]
    total: int


class DiscoverJobsData(BaseModel):
    discovered: int
    created: int
    updated: int
    items: list[JobPublic]
    warnings: list[str] = Field(default_factory=list)


class ApiResponse(BaseModel):
    data: object | None = None
    metadata: dict = Field(default_factory=dict)
    errors: list = Field(default_factory=list)
