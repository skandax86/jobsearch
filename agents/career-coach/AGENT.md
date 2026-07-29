# Career Coach Agent

**Status:** 🔴 planned  
**Agent id:** `career_coach`

## Responsibility

Recommend career moves from feedback, profile, and market signals.

## Inputs

- `profile`
- `feedback`
- `market_signals`

## Outputs

- `recommendations`

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
