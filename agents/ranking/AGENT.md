# Ranking Agent

**Status:** 🟡 partial  
**Agent id:** `ranking`

## Responsibility

Score eligible postings against the candidate profile; explain gaps.

## Inputs

- `candidate_profile`
- `job_postings`
- `resume_content`

## Outputs

- `ranked_matches`
- `scores`
- `gap_rationale`

## MCP tools

- _(none — domain services only)_

## ACP workflows

`job_discovery`

## Runtime

apps/api/src/careerpilot/domains/intelligence/

## Quality rules

- Schema-constrained outputs; validate before downstream use.
- Cite provenance; return uncertainty instead of guessing.
- Respect token / latency / retry budgets from the Supervisor.
- Never call other agents directly — return to ACP.
