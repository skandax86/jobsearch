"""Current user profile routes."""

from __future__ import annotations

from fastapi import APIRouter

from careerpilot.api.deps import CurrentUser
from careerpilot.domains.identity.schemas import (
    ApiResponse,
    CandidateProfilePublic,
    MeData,
    UserPublic,
)

router = APIRouter(tags=["me"])


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
