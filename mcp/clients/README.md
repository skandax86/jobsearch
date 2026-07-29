# MCP clients

How CareerPilot **calls** MCP servers.

## In-process (API)

Preferred for product paths. The API imports server modules and calls tools directly:

```python
from careerpilot.mcp.resume import call_resume_tool
from careerpilot.mcp.linkedin import call_linkedin_tool

result = await call_resume_tool("segment_resume_sections", text=raw_text)
```

Base protocol: `apps/api/src/careerpilot/mcp/base.py` (`McpServer`, `McpToolResult`).

## Cursor / stdio (developer)

Configured in `.cursor/mcp.json`:

| Server | Command |
|--------|---------|
| microsoft-learn | remote URL |
| mcp-server-linkedin | `uvx mcp-server-linkedin@latest` |
| naukri-mcp | `tools/run-naukri-mcp.sh` |

Resume debug CLI (not full MCP stdio protocol):

```bash
./tools/run-resume-mcp.sh list
./tools/run-resume-mcp.sh call structure_resume_heuristic --json '{"text":"..."}'
```

## Client rules

1. Always check `status` before reading `result`.
2. Map `ERROR` codes to domain errors; do not leak provider secrets.
3. Record MCP tool name + latency in agent/workflow telemetry.
