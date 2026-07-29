"""Current user profile routes."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from careerpilot.api.deps import CurrentUser
from careerpilot.db.session import get_db
from careerpilot.domains.identity.schemas import (
    ApiResponse,
    CandidateProfilePublic,
    MeData,
    UserPublic,
)
from careerpilot.domains.resume.schema import normalize_resume_content
from careerpilot.domains.resume.service import (
    ResumeError,
    get_profile_resume_content,
    update_profile_resume_content,
)

router = APIRouter(tags=["me"])

DbSession = Annotated[AsyncSession, Depends(get_db)]


class ProfileResumeData(BaseModel):
    candidate_profile: CandidateProfilePublic
    content: dict[str, Any]


class UpdateProfileResumeRequest(BaseModel):
    content: dict[str, Any] = Field(default_factory=dict)


@router.get("/me", response_model=ApiResponse)
async def get_me(user: CurrentUser) -> ApiResponse:
    profile = user.candidate_profile
    return ApiResponse(
        data=MeData(
            user=UserPublic.model_validate(user),
            candidate_profile=CandidateProfilePublic.model_validate(profile)
            if profile is not None
            else None,
        )
    )


@router.get("/me/profile", response_model=ApiResponse)
async def get_my_profile(user: CurrentUser) -> ApiResponse | JSONResponse:
    profile = user.candidate_profile
    if profile is None:
        return JSONResponse(
            status_code=400,
            content=ApiResponse(
                errors=[{"code": "profile_missing", "message": "Candidate profile is required."}]
            ).model_dump(),
        )
    content = get_profile_resume_content(profile)
    return ApiResponse(
        data=ProfileResumeData(
            candidate_profile=CandidateProfilePublic.model_validate(profile),
            content=content,
        )
    )


@router.put("/me/profile", response_model=ApiResponse)
async def update_my_profile(
    payload: UpdateProfileResumeRequest,
    user: CurrentUser,
    db: DbSession,
) -> ApiResponse | JSONResponse:
    try:
        profile = await update_profile_resume_content(
            db,
            user=user,
            content=normalize_resume_content(payload.content),
        )
    except ResumeError as exc:
        return JSONResponse(
            status_code=400,
            content=ApiResponse(errors=[{"code": exc.code, "message": exc.message}]).model_dump(),
        )
    return ApiResponse(
        data=ProfileResumeData(
            candidate_profile=CandidateProfilePublic.model_validate(profile),
            content=get_profile_resume_content(profile),
        )
    )
