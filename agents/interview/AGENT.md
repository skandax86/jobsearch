# Interview Coach Agent

**Status:** 🔴 planned  
**Agent id:** `interview`

## Responsibility

Build interview prep plans from job, company, and verified profile.

## Inputs

- `interview`
- `company`
- `profile`

## Outputs

- `prep_plan`
- `likely_questions`

## MCP tools

- _(none — domain services only)_

## ACP workflows

_(none yet)_

## Runtime

_Not implemented — spec only._

## Quality rules

- Schema-constrained outputs; validate before downstream use.
- Cite provenance; return uncertainty instead of guessing.
- Respect token / latency / retry budgets from the Supervisor.
- Never call other agents directly — return to ACP.
