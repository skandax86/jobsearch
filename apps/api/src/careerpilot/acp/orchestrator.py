"""Minimal in-process ACP orchestrator (workflow state + task sequencing)."""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Awaitable, Callable

from sqlalchemy.ext.asyncio import AsyncSession

from careerpilot.domains.platform.models import AgentExecution, Workflow, WorkflowTask

logger = logging.getLogger(__name__)

WorkflowHandler = Callable[..., Awaitable["AcpWorkflowResult"]]


@dataclass
class AcpWorkflowResult:
    status: str  # completed | failed | needs_review
    output: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    tasks: list[dict[str, Any]] = field(default_factory=list)


class AcpOrchestrator:
    """Registers and runs ACP workflows; persists Workflow / WorkflowTask / AgentExecution."""

    def __init__(self) -> None:
        self._handlers: dict[str, WorkflowHandler] = {}

    def register(self, workflow_type: str, handler: WorkflowHandler) -> None:
        self._handlers[workflow_type] = handler

    def list_workflows(self) -> list[str]:
        return sorted(self._handlers)

    async def start(
        self,
        db: AsyncSession,
        *,
        user_id: uuid.UUID,
        workflow_type: str,
        input_payload: dict[str, Any],
        correlation_id: str | None = None,
    ) -> tuple[Workflow, AcpWorkflowResult]:
        handler = self._handlers.get(workflow_type)
        if handler is None:
            raise KeyError(f"Unknown ACP workflow: {workflow_type}")

        workflow = Workflow(
            user_id=user_id,
            workflow_type=workflow_type,
            status="running",
            input=input_payload,
            state={"steps": []},
            correlation_id=correlation_id or str(uuid.uuid4()),
        )
        db.add(workflow)
        await db.flush()

        try:
            result = await handler(db, workflow=workflow, input_payload=input_payload)
        except Exception as exc:
            logger.exception("ACP workflow %s crashed", workflow_type)
            workflow.status = "failed"
            workflow.state = {
                **(workflow.state or {}),
                "error": str(exc),
                "finished_at": datetime.now(UTC).isoformat(),
            }
            await db.flush()
            return workflow, AcpWorkflowResult(status="failed", error=str(exc))

        workflow.status = result.status
        workflow.state = {
            **(workflow.state or {}),
            "output_keys": list((result.output or {}).keys()),
            "tasks": result.tasks,
            "finished_at": datetime.now(UTC).isoformat(),
            "error": result.error,
        }
        await db.flush()
        return workflow, result

    async def record_task(
        self,
        db: AsyncSession,
        *,
        workflow: Workflow,
        task_type: str,
        agent_name: str,
        payload: dict[str, Any] | None = None,
        result: dict[str, Any] | None = None,
        status: str = "completed",
        error: str | None = None,
        model: str | None = None,
    ) -> WorkflowTask:
        task = WorkflowTask(
            workflow_id=workflow.id,
            task_type=task_type,
            status=status,
            payload=payload,
            result=result,
            attempt_count=1,
        )
        db.add(task)
        await db.flush()

        now = datetime.now(UTC)
        execution = AgentExecution(
            workflow_id=workflow.id,
            workflow_task_id=task.id,
            agent_name=agent_name,
            model=model,
            status="succeeded" if status == "completed" else "failed",
            error=error,
            started_at=now,
            completed_at=now,
            token_usage=None,
        )
        db.add(execution)
        await db.flush()

        steps = list((workflow.state or {}).get("steps") or [])
        steps.append(
            {
                "task_type": task_type,
                "agent": agent_name,
                "status": status,
                "task_id": str(task.id),
            }
        )
        workflow.state = {**(workflow.state or {}), "steps": steps}
        await db.flush()
        return task


acp = AcpOrchestrator()
