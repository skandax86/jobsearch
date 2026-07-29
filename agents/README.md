# Agents

Production **agent registry** for CareerPilot. Each folder is one specialized agent.

Runtime code (when implemented) lives primarily under:

- `apps/api/src/careerpilot/agents/` — runnable agents
- ACP tasks dispatch here conceptually; MCP tools are the only external I/O path

```text
agents/
├── README.md
├── registry.yaml          ← canonical list
├── supervisor/
├── planner/
├── resume/
├── search/
├── ranking/
├── optimizer/
├── cover-letter/
├── application/
├── tracker/
├── interview/
├── career-coach/
├── recruiter/
└── notification/
```

## Common contract

Every agent:

1. Accepts a typed ACP task (+ authorized refs, policy, budget).
2. Returns `{ result, confidence, warnings, provenance, outcome }`.
3. Does **not** call other agents directly.
4. Does **not** write domain aggregates except via domain services invoked by workflows.
5. Accesses providers only through **MCP**.

## Status legend

| Symbol | Meaning |
|--------|---------|
| ✅ | Implemented / wired |
| 🟡 | Partial |
| 🔴 | Spec only |

## Related docs

- [docs/04-agents/00-Agent-Registry-and-Design.md](../docs/04-agents/00-Agent-Registry-and-Design.md)
- [docs/02-architecture/05-AI-Agent-Layer.md](../docs/02-architecture/05-AI-Agent-Layer.md)
