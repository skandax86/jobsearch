"""ACP JobDiscoveryWorkflow — search providers + LinkedIn connection context."""

from __future__ import annotations

import logging
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from careerpilot.acp.orchestrator import AcpWorkflowResult, acp
from careerpilot.agents.job_discovery import run_job_discovery_agent
from careerpilot.domains.identity.models import User
from careerpilot.domains.jobs.filters import JobSearchFilters
from careerpilot.domains.platform.models import Workflow
from careerpilot.mcp.linkedin.server import call_linkedin_tool

logger = logging.getLogger(__name__)

WORKFLOW_TYPE = "job_discovery"


async def run_job_discovery_workflow(
    db: AsyncSession,
    *,
    workflow: Workflow,
    input_payload: dict[str, Any],
) -> AcpWorkflowResult:
    user_id = input_payload.get("user_id")
    if not user_id:
        return AcpWorkflowResult(status="failed", error="user_id is required.")

    user = await db.get(User, uuid.UUID(str(user_id)))
    if user is None:
        return AcpWorkflowResult(status="failed", error="User not found.")

    task_log: list[dict[str, Any]] = []

    # 1) LinkedIn connection context via MCP
    linkedin = await call_linkedin_tool(
        db,
        tool_name="linkedin_connection_status",
        user_id=user.id,
    )
    await acp.record_task(
        db,
        workflow=workflow,
        task_type="linkedin_status",
        agent_name="search",
        payload={},
        result=linkedin.result if linkedin.status == "SUCCESS" else {},
        status="completed" if linkedin.status == "SUCCESS" else "failed",
        error=(linkedin.error or {}).get("message") if linkedin.error else None,
    )
    task_log.append({"step": "linkedin_status", "status": linkedin.status})

    linkedin_profile = None
    if linkedin.status == "SUCCESS" and (linkedin.result or {}).get("connected"):
        profile_res = await call_linkedin_tool(
            db,
            tool_name="linkedin_get_profile",
            user_id=user.id,
        )
        await acp.record_task(
            db,
            workflow=workflow,
            task_type="linkedin_profile",
            agent_name="search",
            payload={},
            result={"ok": profile_res.status == "SUCCESS"},
            status="completed" if profile_res.status == "SUCCESS" else "failed",
            error=(profile_res.error or {}).get("message") if profile_res.error else None,
        )
        task_log.append({"step": "linkedin_profile", "status": profile_res.status})
        if profile_res.status == "SUCCESS":
            linkedin_profile = profile_res.result

    # 2) Provider discovery (domain service)
    filters = JobSearchFilters(
        query=input_payload.get("query"),
        location=input_payload.get("location"),
        country=input_payload.get("country"),
        remote_type=input_payload.get("remote_type"),
        skills=list(input_payload.get("skills") or []),
        experience_level=input_payload.get("experience_level"),
        min_experience_years=input_payload.get("min_experience_years"),
        include_demo=bool(input_payload.get("include_demo", True)),
        include_remotive=bool(input_payload.get("include_remotive", True)),
        include_naukri=bool(input_payload.get("include_naukri", False)),
        limit=int(input_payload.get("limit") or 20),
    )
    discovery = await run_job_discovery_agent(db, user=user, filters=filters)
    await acp.record_task(
        db,
        workflow=workflow,
        task_type="search_providers",
        agent_name="search",
        payload={"providers": [t.get("result", {}).get("providers") for t in discovery.get("tool_trace") or []]},
        result={
            "discovered": discovery.get("discovered"),
            "created": discovery.get("created"),
            "updated": discovery.get("updated"),
            "item_count": len(discovery.get("items") or []),
        },
        status="completed",
    )
    task_log.append({"step": "search_providers", "status": "SUCCESS"})

    # 3) Lightweight ranking preview (scores already exist via matches API; record stub complete)
    await acp.record_task(
        db,
        workflow=workflow,
        task_type="rank_preview",
        agent_name="ranking",
        payload={},
        result={"note": "Full scoring via POST /api/v1/matches/run"},
        status="completed",
    )
    task_log.append({"step": "rank_preview", "status": "SUCCESS"})

    items = discovery.get("items") or []
    # Serialize ORM jobs lightly for workflow output
    item_ids = [str(getattr(j, "id", j)) for j in items]

    return AcpWorkflowResult(
        status="completed",
        output={
            **{k: v for k, v in discovery.items() if k != "items"},
            "item_ids": item_ids,
            "linkedin_connected": bool((linkedin.result or {}).get("connected")),
            "linkedin_profile": linkedin_profile,
            "orchestration": "acp+mcp",
        },
        tasks=task_log,
    )


async def start_job_discovery(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    filters: dict[str, Any],
    correlation_id: str | None = None,
) -> tuple[Workflow, AcpWorkflowResult]:
    return await acp.start(
        db,
        user_id=user_id,
        workflow_type=WORKFLOW_TYPE,
        input_payload={"user_id": str(user_id), **filters},
        correlation_id=correlation_id,
    )


acp.register(WORKFLOW_TYPE, run_job_discovery_workflow)
