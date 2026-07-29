# MCP server: linkedin

**Status:** 🟡 partial

## Runtimes

| Path | Role |
|------|------|
| `apps/api/src/careerpilot/mcp/linkedin/` | In-process OAuth tools (connection status, OpenID profile) |
| Cursor `mcp-server-linkedin` | Personal browser session (search jobs, messaging) |

## In-process tools

| Tool | Description |
|------|-------------|
| `linkedin_connection_status` | Active OAuth? |
| `linkedin_get_profile` | OpenID profile |
| `linkedin_search_jobs` | Partner-gated / unsupported without Jobs API |

## Cursor tools (developer)

See LinkedIn MCP server docs — `search_jobs`, `get_job_details`, `get_my_profile`, etc.

## Policy

Jobs API is partner-gated. Product discovery prefers Remotive/Naukri/demo; LinkedIn browser MCP is optional for local agents.
