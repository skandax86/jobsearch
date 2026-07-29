# Supervisor Agent

**Status:** 🔴 planned  
**Agent id:** `supervisor`

## Responsibility

Monitor workflows, apply timeouts/budgets, pause for human approval, retry or escalate failures.

## Inputs

- `workflow_state`
- `policy`
- `budgets`

## Outputs

- `route`
- `retry`
- `escalation`
- `approval_request`

## MCP tools

- _(none — domain services only)_

## ACP workflows

`tailor_resume`, `apply_job`

## Runtime

_Not implemented — spec only._

## Quality rules

- Schema-constrained outputs; validate before downstream use.
- Cite provenance; return uncertainty instead of guessing.
- Respect token / latency / retry budgets from the Supervisor.
- Never call other agents directly — return to ACP.
