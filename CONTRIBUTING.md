# Contributing

## Repo layout (contracts vs runtime)

| Path | Role |
|------|------|
| `acp/` | ACP workflow/message **contracts** (YAML + JSON Schema) |
| `agents/` | Agent **registry** + per-agent specs (`AGENT.md`) |
| `mcp/` | MCP server/client **contracts** + tool inventories |
| `apps/api/` | FastAPI **runtime** (orchestrator, agents, MCP servers) |
| `apps/web/` | Next.js UI |
| `docs/` | Architecture & product specifications |
| `tools/` | Local CLIs (Naukri MCP, resume MCP debug) |

Contracts in `acp/`, `agents/`, and `mcp/` describe what should exist. Python under `apps/api/src/careerpilot/{acp,agents,mcp}/` is what runs in production/dev.

## Adding a capability

1. Spec the MCP tool under `mcp/servers/<name>/`.
2. Spec the agent under `agents/<name>/AGENT.md` and update `agents/registry.yaml`.
3. Spec the ACP workflow under `acp/workflows/`.
4. Implement runtime in `apps/api` and register the workflow with `acp.register(...)`.
5. Add tests under `apps/api/tests/`.

## Local checks

```bash
make up && make migrate
make check-contracts
make api   # terminal 1
make web   # terminal 2
cd apps/api && PYTHONPATH=src pytest -q
./tools/run-resume-mcp.sh list
```
