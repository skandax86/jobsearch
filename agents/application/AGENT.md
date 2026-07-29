# Application Agent

**Status:** 🔴 planned  
**Agent id:** `application`

## Responsibility

Assemble and submit an approved application package via ATS MCP tools.

## Inputs

- `approved_package`
- `job_posting`
- `policy`

## Outputs

- `submission_evidence`
- `application_id`

## MCP tools

- `naukri.apply_job`
- `naukri.approve_job`

## ACP workflows

`apply_job`

## Runtime

_Not implemented — spec only._

## Quality rules

- Schema-constrained outputs; validate before downstream use.
- Cite provenance; return uncertainty instead of guessing.
- Respect token / latency / retry budgets from the Supervisor.
- Never call other agents directly — return to ACP.
