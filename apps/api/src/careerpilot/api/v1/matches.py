"""Matches routes — run scoring, list, get."""

from __future__ import annotations

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from careerpilot.api.deps import CurrentUser
from careerpilot.db.session import get_db
from careerpilot.domains.intelligence.schemas import (
    ApiResponse,
    MatchListData,
    MatchPublic,
    RunMatchingData,
    RunMatchingRequest,
)
from careerpilot.domains.intelligence.service import (
    MatchError,
    get_match,
    list_matches,
    run_matching,
)
from careerpilot.domains.jobs.schemas import JobPublic

router = APIRouter(prefix="/matches", tags=["matches"])

DbSession = Annotated[AsyncSession, Depends(get_db)]


def _error(status_code: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=ApiResponse(errors=[{"code": code, "message": message}]).model_dump(),
    )


def _match_public(match: Any) -> MatchPublic:
    job = getattr(match, "job_posting", None)
    return MatchPublic(
        id=match.id,
        score=match.score,
        confidence=match.confidence,
        explanation=match.explanation,
        features=match.features,
        model_version=match.model_version,
        resume_version_id=match.resume_version_id,
        job_posting_id=match.job_posting_id,
        job=JobPublic.model_validate(job) if job is not None else None,
        created_at=match.created_at,
        updated_at=match.updated_at,
    )


@router.post("/run")
async def run_matches(
    payload: RunMatchingRequest,
    user: CurrentUser,
    db: DbSession,
) -> JSONResponse:
    try:
        result = await run_matching(
            db,
            user=user,
            resume_id=payload.resume_id,
            limit=payload.limit,
            min_score=payload.min_score,
        )
    except MatchError as exc:
        code_map = {
            "profile_missing": status.HTTP_400_BAD_REQUEST,
            "resume_missing": status.HTTP_400_BAD_REQUEST,
            "resume_not_parsed": status.HTTP_400_BAD_REQUEST,
            "jobs_missing": status.HTTP_400_BAD_REQUEST,
        }
        return _error(
            code_map.get(exc.code, status.HTTP_400_BAD_REQUEST),
            exc.code,
            exc.message,
        )

    body = ApiResponse(
        data=RunMatchingData(
            resume_id=result["resume_id"],
            resume_version_id=result["resume_version_id"],
            model_version=result["model_version"],
            scored=result["scored"],
            matched=result["matched"],
            items=[_match_public(m) for m in result["items"]],
        )
    )
    return JSONResponse(content=body.model_dump(mode="json"))


@router.get("")
async def list_my_matches(
    user: CurrentUser,
    db: DbSession,
    min_score: Annotated[float, Query(ge=0.0, le=1.0)] = 0.0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> JSONResponse:
    items, total = await list_matches(
        db, user=user, min_score=min_score, limit=limit, offset=offset
    )
    body = ApiResponse(data=MatchListData(items=[_match_public(m) for m in items], total=total))
    return JSONResponse(content=body.model_dump(mode="json"))


@router.get("/{match_id}")
async def get_my_match(
    match_id: uuid.UUID,
    user: CurrentUser,
    db: DbSession,
) -> JSONResponse:
    try:
        match = await get_match(db, user=user, match_id=match_id)
    except MatchError as exc:
        code = status.HTTP_404_NOT_FOUND if exc.code == "not_found" else status.HTTP_400_BAD_REQUEST
        return _error(code, exc.code, exc.message)
    body = ApiResponse(data=_match_public(match))
    return JSONResponse(content=body.model_dump(mode="json"))
