# MCP server: resume

**Status:** ✅ implemented (in-process)

**Runtime:** `apps/api/src/careerpilot/mcp/resume/`

**Used by ACP:** `resume_parse`

## Tools

| Tool | Description |
|------|-------------|
| `extract_resume_text` | PDF/DOCX → plain text (`data_b64` + `mime_type`) |
| `segment_resume_sections` | Rule-based section boundaries |
| `structure_resume_heuristic` | ATS rule extract → resume JSON 1.1 |
| `structure_resume_ai` | LLM extract (OpenAI-compatible / LM Studio) |
| `validate_resume_json` | Confidence + needs_review flags |

## Contract file

See [tools.json](./tools.json)

## Test

```bash
curl -s -b cookies.txt http://localhost:8000/api/v1/agents/mcp/resume/tools | jq
./tools/run-resume-mcp.sh list
```
