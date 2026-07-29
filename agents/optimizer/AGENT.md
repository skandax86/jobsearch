# Resume Optimizer Agent

**Status:** 🟡 partial  
**Agent id:** `optimizer`

## Responsibility

Propose job-specific resume edits without inventing experience. Factual changes require approval.

## Inputs

- `resume_content`
- `job_posting`

## Outputs

- `suggestions`
- `proposed_content`

## MCP tools

- _(none — domain services only)_

## ACP workflows

`tailor_resume`

## Runtime

apps/api/src/careerpilot/domains/resume/tailor.py

## Quality rules

- Schema-constrained outputs; validate before downstream use.
- Cite provenance; return uncertainty instead of guessing.
- Respect token / latency / retry budgets from the Supervisor.
- Never call other agents directly — return to ACP.
