# Planner Agent

**Status:** 🔴 planned  
**Agent id:** `planner`

## Responsibility

Select permitted workflow steps from user intent and automation policy. Produce a plan only — no side effects.

## Inputs

- `user_intent`
- `automation_policy`
- `available_workflows`

## Outputs

- `workflow_plan`
- `constraints`
- `budget`

## MCP tools

- _(none — domain services only)_

## ACP workflows

`job_discovery`, `tailor_resume`, `apply_job`

## Runtime

_Not implemented — spec only._

## Quality rules

- Schema-constrained outputs; validate before downstream use.
- Cite provenance; return uncertainty instead of guessing.
- Respect token / latency / retry budgets from the Supervisor.
- Never call other agents directly — return to ACP.
