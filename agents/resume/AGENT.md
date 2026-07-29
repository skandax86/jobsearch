# Resume Agent

**Status:** ✅ implemented (parse path)  
**Agent id:** `resume`

## Responsibility

Extract and structure resume content into CareerPilot schema via resume MCP tools. Propose facts; flag low-confidence for review.

## Inputs

- `source_bytes`
- `mime_type`
- `resume_id`

## Outputs

- `resume_content_v1.1`
- `confidence`
- `parser`
- `needs_review`

## MCP tools

- `extract_resume_text`
- `segment_resume_sections`
- `structure_resume_heuristic`
- `structure_resume_ai`
- `validate_resume_json`

## ACP workflows

`resume_parse`, `tailor_resume`

## Runtime

apps/api/src/careerpilot/acp/workflows/resume_parse.py + mcp/resume

## Quality rules

- Schema-constrained outputs; validate before downstream use.
- Cite provenance; return uncertainty instead of guessing.
- Respect token / latency / retry budgets from the Supervisor.
- Never call other agents directly — return to ACP.
