# Cover Letter Agent

**Status:** 🟡 partial  
**Agent id:** `cover_letter`

## Responsibility

Draft a job-specific cover letter from verified profile facts only.

## Inputs

- `verified_profile`
- `job_posting`
- `tone`

## Outputs

- `draft_letter`
- `highlights`

## MCP tools

- _(none — domain services only)_

## ACP workflows

`tailor_resume`, `apply_job`

## Runtime

cover-letter paths in resume/jobs API (if present)

## Quality rules

- Schema-constrained outputs; validate before downstream use.
- Cite provenance; return uncertainty instead of guessing.
- Respect token / latency / retry budgets from the Supervisor.
- Never call other agents directly — return to ACP.
