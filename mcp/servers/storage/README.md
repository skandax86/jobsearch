# MCP server: storage

**Status:** implemented (in-process)

**Runtime:** `apps/api/src/careerpilot/mcp/storage/server.py`

## Tools

| Tool | Description |
|------|-------------|
| `put_object` | Store bytes (base64) at an object key |
| `get_object` | Read object bytes by key (base64) |

Resume upload/parse uses storage MCP with a direct MinIO adapter fallback.
