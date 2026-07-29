"""Agent run endpoints + ACP / MCP introspection."""

from __future__ import annotations

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from careerpilot.api.deps import CurrentUser
from careerpilot.db.session import get_db
from careerpilot.domains.identity.schemas import ApiResponse
from careerpilot.domains.jobs.filters import JobSearchFilters
from careerpilot.domains.jobs.models import JobPosting
from careerpilot.domains.jobs.schemas import JobPublic
from careerpilot.domains.platform.models import Workflow

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


class TailorWorkflowRequest(BaseModel):
    resume_id: uuid.UUID
    job_posting_id: uuid.UUID | None = None
    job_title: str | None = Field(default=None, max_length=255)
    job_description: str | None = None
    company_name: str | None = Field(default=None, max_length=255)


def _ensure_workflows_registered() -> None:
    import careerpilot.acp.workflows  # noqa: F401


@router.post("/job-discovery/run")
async def run_job_discovery(
    payload: JobDiscoveryAgentRequest,
    user: CurrentUser,
    db: DbSession,
) -> JSONResponse:
    _ensure_workflows_registered()
    from careerpilot.acp.workflows.job_discovery import start_job_discovery

    filters = JobSearchFilters.from_payload(payload)
    workflow, result = await start_job_discovery(
        db,
        user_id=user.id,
        filters={
            "query": filters.query,
            "location": filters.location,
            "country": filters.country,
            "remote_type": filters.remote_type,
            "skills": filters.skills,
            "experience_level": filters.experience_level,
            "min_experience_years": filters.min_experience_years,
            "include_demo": filters.include_demo,
            "include_remotive": filters.include_remotive,
            "include_naukri": filters.include_naukri,
            "limit": filters.limit,
        },
    )
    await db.commit()

    if result.status == "failed":
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=ApiResponse(
                errors=[{"code": "workflow_failed", "message": result.error or "Job discovery failed."}]
            ).model_dump(),
        )

    item_ids = [uuid.UUID(str(i)) for i in (result.output or {}).get("item_ids") or []]
    jobs: list[JobPosting] = []
    if item_ids:
        jobs = list(
            await db.scalars(
                select(JobPosting)
                .where(JobPosting.id.in_(item_ids))
                .options(selectinload(JobPosting.company), selectinload(JobPosting.sources))
            )
        )
        order = {jid: idx for idx, jid in enumerate(item_ids)}
        jobs.sort(key=lambda j: order.get(j.id, 10_000))

    items = [JobPublic.model_validate(job).model_dump(mode="json") for job in jobs]
    data: dict[str, Any] = {
        **{k: v for k, v in (result.output or {}).items() if k not in {"item_ids", "linkedin_profile"}},
        "items": items,
        "workflow_id": str(workflow.id),
        "workflow_status": result.status,
        "acp_tasks": result.tasks,
    }
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


@router.get("/mcp/storage/tools")
async def list_storage_mcp_tools(user: CurrentUser) -> JSONResponse:
    _ = user
    from careerpilot.mcp.storage.server import storage_mcp

    return JSONResponse(
        content=ApiResponse(
            data={"server": "storage", "tools": storage_mcp.list_tools()}
        ).model_dump()
    )


@router.get("/acp/workflows")
async def list_acp_workflows(user: CurrentUser) -> JSONResponse:
    _ = user
    from careerpilot.acp.orchestrator import acp

    _ensure_workflows_registered()
    return JSONResponse(
        content=ApiResponse(data={"workflows": acp.list_workflows()}).model_dump()
    )


@router.post("/acp/workflows/{workflow_type}/start")
async def start_acp_workflow(
    workflow_type: str,
    payload: dict[str, Any],
    user: CurrentUser,
    db: DbSession,
) -> JSONResponse:
    from careerpilot.acp.orchestrator import acp

    _ensure_workflows_registered()
    if workflow_type not in acp.list_workflows():
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=ApiResponse(
                errors=[{"code": "unknown_workflow", "message": f"Unknown workflow: {workflow_type}"}]
            ).model_dump(),
        )

    try:
        if workflow_type == "job_discovery":
            from careerpilot.acp.workflows.job_discovery import start_job_discovery

            workflow, result = await start_job_discovery(
                db, user_id=user.id, filters=payload or {}
            )
        elif workflow_type == "tailor_resume":
            from careerpilot.acp.workflows.tailor_resume import start_tailor_resume

            resume_id = payload.get("resume_id")
            if not resume_id:
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content=ApiResponse(
                        errors=[{"code": "resume_id_required", "message": "resume_id is required."}]
                    ).model_dump(),
                )
            workflow, result = await start_tailor_resume(
                db,
                user_id=user.id,
                resume_id=uuid.UUID(str(resume_id)),
                payload={k: v for k, v in payload.items() if k != "resume_id"},
            )
        elif workflow_type == "resume_parse":
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=ApiResponse(
                    errors=[
                        {
                            "code": "use_resume_parse_endpoint",
                            "message": "Use POST /api/v1/resumes/{id}/parse for resume_parse.",
                        }
                    ]
                ).model_dump(),
            )
        else:
            workflow, result = await acp.start(
                db,
                user_id=user.id,
                workflow_type=workflow_type,
                input_payload=payload or {},
            )
        await db.commit()
    except ValueError as exc:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=ApiResponse(errors=[{"code": "invalid_input", "message": str(exc)}]).model_dump(),
        )
    except KeyError as exc:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=ApiResponse(errors=[{"code": "unknown_workflow", "message": str(exc)}]).model_dump(),
        )

    return JSONResponse(
        content=ApiResponse(
            data={
                "workflow_id": str(workflow.id),
                "workflow_type": workflow.workflow_type,
                "status": result.status,
                "output": result.output,
                "error": result.error,
                "tasks": result.tasks,
            }
        ).model_dump(mode="json")
    )


@router.get("/acp/workflows/runs/{workflow_id}")
async def get_acp_workflow_run(
    workflow_id: uuid.UUID,
    user: CurrentUser,
    db: DbSession,
) -> JSONResponse:
    workflow = await db.scalar(
        select(Workflow).where(Workflow.id == workflow_id, Workflow.user_id == user.id)
    )
    if workflow is None:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=ApiResponse(
                errors=[{"code": "not_found", "message": "Workflow run not found."}]
            ).model_dump(),
        )
    return JSONResponse(
        content=ApiResponse(
            data={
                "workflow_id": str(workflow.id),
                "workflow_type": workflow.workflow_type,
                "status": workflow.status,
                "input": workflow.input,
                "state": workflow.state,
                "correlation_id": workflow.correlation_id,
                "created_at": workflow.created_at.isoformat() if workflow.created_at else None,
                "updated_at": workflow.updated_at.isoformat() if workflow.updated_at else None,
            }
        ).model_dump(mode="json")
    )


@router.post("/acp/workflows/tailor_resume/run")
async def run_tailor_resume_workflow(
    payload: TailorWorkflowRequest,
    user: CurrentUser,
    db: DbSession,
) -> JSONResponse:
    """Convenience endpoint matching product tailor flow via ACP."""
    _ensure_workflows_registered()
    from careerpilot.acp.workflows.tailor_resume import start_tailor_resume

    try:
        workflow, result = await start_tailor_resume(
            db,
            user_id=user.id,
            resume_id=payload.resume_id,
            payload=payload.model_dump(mode="json", exclude={"resume_id"}),
        )
        await db.commit()
    except ValueError as exc:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=ApiResponse(errors=[{"code": "invalid_input", "message": str(exc)}]).model_dump(),
        )

    if result.status == "failed":
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=ApiResponse(
                errors=[{"code": "workflow_failed", "message": result.error or "Tailor failed."}]
            ).model_dump(),
        )

    return JSONResponse(
        content=ApiResponse(
            data={
                "workflow_id": str(workflow.id),
                "status": result.status,
                **(result.output or {}),
                "acp_tasks": result.tasks,
            }
        ).model_dump(mode="json")
    )
