# ACP Orchestrator

## Responsibility

Own workflow lifecycle: create → run tasks → record agent executions → complete / fail / needs_review.

## Runtime

| Item | Location |
|------|----------|
| In-process orchestrator | `apps/api/src/careerpilot/acp/orchestrator.py` |
| Global registry | `acp = AcpOrchestrator()` |
| Persist models | `Workflow`, `WorkflowTask`, `AgentExecution` |

## Contract

```text
start(db, user_id, workflow_type, input_payload, correlation_id?)
  → (Workflow, AcpWorkflowResult)

record_task(db, workflow, task_type, agent_name, payload?, result?, status, error?, model?)
  → WorkflowTask
```

### `AcpWorkflowResult`

| Field | Type | Meaning |
|-------|------|---------|
| `status` | `completed` \| `failed` \| `needs_review` | Terminal workflow status |
| `output` | object | Workflow-specific payload |
| `error` | string \| null | Failure message |
| `tasks` | array | Step summary for provenance |

## Rules

1. Unknown `workflow_type` → error (do not invent handlers).
2. Every MCP/tool call from a workflow must be preceded or followed by `record_task`.
3. Side effects (DB writes for domain entities) stay in domain services, not the orchestrator.
4. Idempotency keys should use `correlation_id` (e.g. resume id).

## Registering a workflow

```python
from careerpilot.acp.orchestrator import acp

async def my_handler(db, *, workflow, input_payload):
    ...
    return AcpWorkflowResult(status="completed", output={...})

acp.register("my_workflow", my_handler)
```
