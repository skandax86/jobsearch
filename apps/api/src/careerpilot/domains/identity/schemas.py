"""Identity API schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    display_name: str | None = Field(default=None, max_length=255)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class UserPublic(BaseModel):
    id: uuid.UUID
    email: str
    display_name: str | None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class CandidateProfilePublic(BaseModel):
    id: uuid.UUID
    headline: str | None = None
    preferences_version: int

    model_config = {"from_attributes": True}


class AuthData(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime
    user: UserPublic
    candidate_profile: CandidateProfilePublic


class MeData(BaseModel):
    user: UserPublic
    candidate_profile: CandidateProfilePublic | None


class ApiResponse(BaseModel):
    data: object | None = None
    metadata: dict = Field(default_factory=dict)
    errors: list = Field(default_factory=list)
