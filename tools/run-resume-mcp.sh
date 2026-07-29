#!/usr/bin/env bash
# Resume MCP debug CLI (in-process tools).
# Production parsing: API → ACP resume_parse → these MCP tools.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/apps/api"
exec uv run python -m careerpilot.mcp.resume.stdio "$@"
