# ACP (Agent Communication Protocol)

Top-level **contracts** for CareerPilot agent orchestration.

Runtime implementation lives in the API:

`apps/api/src/careerpilot/acp/`

```text
acp/
├── README.md                 ← this file
├── orchestrator/             ← orchestrator contract + API mapping
├── workflows/                ← durable workflow definitions
├── messages/                 ← typed ACP message envelopes
└── schemas/                  ← JSON Schema for messages / results
```

## Principles

- ACP coordinates **agents** (routing, retries, approvals, state).
- MCP exposes **tools** (PDF, LinkedIn, Naukri, storage).
- Agents never call each other directly; they receive ACP tasks.
- Workflows persist to `workflows` / `workflow_tasks` / `agent_executions`.

## Implemented today

| Workflow | Status | Runtime |
|----------|--------|---------|
| `resume_parse` | ✅ | `careerpilot.acp.workflows.resume_parse` |

## Planned

| Workflow | Agents | Notes |
|----------|--------|-------|
| `job_discovery` | planner → search → ranking | Partial agent exists (`job_discovery`) |
| `tailor_resume` | resume → optimizer | Tailor API exists; not ACP-wrapped yet |
| `apply_job` | application + approval | Requires human gate |
| `track_applications` | tracker + notification | Future |

## Quick test

```bash
curl -s -b cookies.txt http://localhost:8000/api/v1/agents/acp/workflows | jq
```

## Related docs

- [docs/06-acp/00-ACP-Specification.md](../docs/06-acp/00-ACP-Specification.md)
- [docs/02-architecture/06-ACP-Architecture.md](../docs/02-architecture/06-ACP-Architecture.md)
