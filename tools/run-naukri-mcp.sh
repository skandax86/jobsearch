#!/usr/bin/env bash
# Launch sanjeev-txt/Naukri-MCP for Cursor (stdio).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/naukri-mcp" && pwd)"
if [[ ! -x "$ROOT/.venv/bin/python" ]]; then
  echo "Naukri MCP not installed. Run: make naukri-mcp-setup" >&2
  exit 1
fi
cd "$ROOT"

# NaukriMCPServer does float(os.getenv(...)); empty strings from envFile crash.
# Coalesce blank numeric env vars to 0 before starting.
_numeric_defaults=(
  CANDIDATE_CURRENT_CTC
  CANDIDATE_EXPECTED_CTC
  CANDIDATE_NOTICE_DAYS
  CANDIDATE_EXPERIENCE_YEARS
  REQUEST_DELAY_SECONDS
  MAX_APPLICATIONS_PER_SESSION
)
for key in "${_numeric_defaults[@]}"; do
  val="${!key-}"
  if [[ -z "${val}" ]]; then
    export "$key=0"
  fi
done

export PYTHONUNBUFFERED=1
exec "$ROOT/.venv/bin/python" server.py
