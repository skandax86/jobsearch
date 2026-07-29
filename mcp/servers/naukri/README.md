# MCP server: naukri

**Status:** 🟡 partial (external package + Cursor)

**Runtime:** `tools/naukri-mcp/` via `tools/run-naukri-mcp.sh`  
**API provider wrapper:** `apps/api/src/careerpilot/domains/jobs/providers/naukri.py`

## Notable tools

| Tool | Side effect |
|------|-------------|
| `search_jobs` | read |
| `get_job_details` | read |
| `apply_job` | write — requires approval policy |
| `bulk_apply` | write — requires approval policy |
| `generate_and_upload_resume` | write |
| `sync_application_statuses` | read/write |

## Setup

```bash
make naukri-mcp-setup
# fill .env.naukri
```

## Policy

Never auto-submit applications without an ACP human gate (`apply_job` workflow).
