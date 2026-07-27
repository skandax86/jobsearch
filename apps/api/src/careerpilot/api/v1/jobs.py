"""Jobs routes — discover, list, get."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from careerpilot.api.deps import CurrentUser
from careerpilot.db.session import get_db
from careerpilot.domains.jobs.filters import JobSearchFilters
from careerpilot.domains.jobs.providers.naukri import naukri_available
from careerpilot.domains.jobs.schemas import (
    ApiResponse,
    DiscoverJobsData,
    DiscoverJobsRequest,
    JobListData,
    JobPublic,
)
from careerpilot.domains.jobs.service import JobError, discover_jobs, get_job, list_jobs

router = APIRouter(prefix="/jobs", tags=["jobs"])

DbSession = Annotated[AsyncSession, Depends(get_db)]


def _error(status_code: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=ApiResponse(errors=[{"code": code, "message": message}]).model_dump(),
    )


def _job_public(job) -> JobPublic:
    return JobPublic.model_validate(job)


def _skills_from_query(skills: str | None) -> list[str]:
    if not skills:
        return []
    return [s.strip() for s in skills.split(",") if s.strip()]


@router.get("/providers")
async def job_providers_status(user: CurrentUser) -> JSONResponse:
    _ = user
    naukri = naukri_available()
    body = ApiResponse(
        data={
            "demo": {"provider": "demo", "ready": True},
            "remotive": {"provider": "remotive", "ready": True},
            "naukri": naukri,
        }
    )
    return JSONResponse(content=body.model_dump(mode="json"))


@router.post("/discover")
async def discover(
    payload: DiscoverJobsRequest,
    user: CurrentUser,
    db: DbSession,
) -> JSONResponse:
    _ = user
    filters = JobSearchFilters.from_payload(payload)
    result = await discover_jobs(db, filters=filters)
    body = ApiResponse(
        data=DiscoverJobsData(
            discovered=result["discovered"],
            created=result["created"],
            updated=result["updated"],
            items=[_job_public(job) for job in result["items"]],
            warnings=list(result.get("warnings") or []),
        )
    )
    return JSONResponse(content=body.model_dump(mode="json"))


@router.get("")
async def list_my_jobs(
    user: CurrentUser,
    db: DbSession,
    q: Annotated[str | None, Query(max_length=200)] = None,
    location: Annotated[str | None, Query(max_length=200)] = None,
    country: Annotated[str | None, Query(max_length=100)] = None,
    remote_type: Annotated[str | None, Query()] = None,
    skills: Annotated[str | None, Query(description="Comma-separated skills")] = None,
    experience_level: Annotated[str | None, Query()] = None,
    min_experience_years: Annotated[int | None, Query(ge=0, le=40)] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> JSONResponse:
    _ = user
    filters = JobSearchFilters(
        query=q,
        location=location,
        country=country,
        remote_type=remote_type,
        skills=_skills_from_query(skills),
        experience_level=experience_level,
        min_experience_years=min_experience_years,
        limit=limit,
    )
    items, total = await list_jobs(db, filters=filters, limit=limit, offset=offset)
    body = ApiResponse(data=JobListData(items=[_job_public(job) for job in items], total=total))
    return JSONResponse(content=body.model_dump(mode="json"))


@router.get("/{job_id}")
async def get_my_job(
    job_id: uuid.UUID,
    user: CurrentUser,
    db: DbSession,
) -> JSONResponse:
    _ = user
    try:
        job = await get_job(db, job_id=job_id)
    except JobError as exc:
        code = status.HTTP_404_NOT_FOUND if exc.code == "not_found" else status.HTTP_400_BAD_REQUEST
        return _error(code, exc.code, exc.message)
    body = ApiResponse(data=_job_public(job))
    return JSONResponse(content=body.model_dump(mode="json"))
