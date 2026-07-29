# MCP (Model Context Protocol)

Top-level **integration boundary** for CareerPilot. Agents reach the outside world only through MCP servers.

```text
mcp/
├── README.md
├── shared/          ← common types / error codes
├── clients/         ← how the API/ACP calls MCP
└── servers/         ← one folder per MCP server
    ├── resume/
    ├── linkedin/
    ├── naukri/
    ├── storage/
    ├── gmail/       (planned)
    └── calendar/    (planned)
```

## Runtime map

| Server | Spec (this tree) | Runtime |
|--------|------------------|---------|
| resume | `servers/resume/` | `apps/api/src/careerpilot/mcp/resume/` (in-process) |
| linkedin | `servers/linkedin/` | `apps/api/src/careerpilot/mcp/linkedin/` + Cursor `mcp-server-linkedin` |
| naukri | `servers/naukri/` | `tools/naukri-mcp/` + Cursor `.cursor/mcp.json` |
| storage | `servers/storage/` | `apps/api/src/careerpilot/storage.py` (domain adapter today) |

## Rules

1. Agents never call LinkedIn/Naukri/S3 HTTP clients directly.
2. Every tool has JSON in/out, timeouts, and normalized errors.
3. Side-effect tools require policy / human approval when marked.
4. Cursor MCP (`.cursor/mcp.json`) is for **developer** tooling; product paths use the API in-process servers.

## Quick test

```bash
curl -s -b cookies.txt http://localhost:8000/api/v1/agents/mcp/resume/tools | jq
./tools/run-resume-mcp.sh list
```

## Related docs

- [docs/05-mcp/00-MCP-Inventory.md](../docs/05-mcp/00-MCP-Inventory.md)
- [docs/02-architecture/07-MCP-Architecture.md](../docs/02-architecture/07-MCP-Architecture.md)
