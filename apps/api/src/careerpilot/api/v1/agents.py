"""Agent run endpoints."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from careerpilot.agents.job_discovery import run_job_discovery_agent
from careerpilot.api.deps import CurrentUser
from careerpilot.db.session import get_db
from careerpilot.domains.identity.schemas import ApiResponse
from careerpilot.domains.jobs.filters import JobSearchFilters
from careerpilot.domains.jobs.schemas import JobPublic

router = APIRouter(prefix="/agents", tags=["agents"])

DbSession = Annotated[AsyncSession, Depends(get_db)]


class JobDiscoveryAgentRequest(BaseModel):
    query: str | None = Field(default=None, max_length=200)
    location: str | None = Field(default=None, max_length=200)
    country: str | None = Field(default=None, max_length=100)
    remote_type: str | None = None
    skills: list[str] = Field(default_factory=list, max_length=20)
    experience_level: str | None = None
    min_experience_years: int | None = Field(default=None, ge=0, le=40)
    include_demo: bool = True
    include_remotive: bool = True
    include_naukri: bool = False
    limit: int = Field(default=20, ge=1, le=50)


@router.post("/job-discovery/run")
async def run_job_discovery(
    payload: JobDiscoveryAgentRequest,
    user: CurrentUser,
    db: DbSession,
) -> JSONResponse:
    filters = JobSearchFilters.from_payload(payload)
    result = await run_job_discovery_agent(db, user=user, filters=filters)
    items = [JobPublic.model_validate(job).model_dump(mode="json") for job in result["items"]]
    data: dict[str, Any] = {**result, "items": items}
    return JSONResponse(content=ApiResponse(data=data).model_dump(mode="json"))


@router.get("/mcp/linkedin/tools")
async def list_linkedin_mcp_tools(user: CurrentUser) -> JSONResponse:
    _ = user
    from careerpilot.mcp.linkedin.server import linkedin_mcp

    return JSONResponse(
        content=ApiResponse(
            data={"server": "linkedin", "tools": linkedin_mcp.list_tools()}
        ).model_dump()
    )


@router.get("/mcp/resume/tools")
async def list_resume_mcp_tools(user: CurrentUser) -> JSONResponse:
    _ = user
    from careerpilot.mcp.resume.server import resume_mcp

    return JSONResponse(
        content=ApiResponse(
            data={"server": "resume", "tools": resume_mcp.list_tools()}
        ).model_dump()
    )


@router.get("/acp/workflows")
async def list_acp_workflows(user: CurrentUser) -> JSONResponse:
    _ = user
    from careerpilot.acp.orchestrator import acp
    # Ensure resume workflow is registered.
    import careerpilot.acp.workflows.resume_parse  # noqa: F401

    return JSONResponse(
        content=ApiResponse(
            data={"workflows": acp.list_workflows()}
        ).model_dump()
    )
