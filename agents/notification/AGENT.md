# Notification Agent

**Status:** 🔴 planned  
**Agent id:** `notification`

## Responsibility

Deliver approved notices on user-preferred channels.

## Inputs

- `event`
- `channel_preferences`

## Outputs

- `delivery_result`

## MCP tools

- `gmail (future)`
- `calendar (future)`

## ACP workflows

`apply_job`

## Runtime

_Not implemented — spec only._

## Quality rules

- Schema-constrained outputs; validate before downstream use.
- Cite provenance; return uncertainty instead of guessing.
- Respect token / latency / retry budgets from the Supervisor.
- Never call other agents directly — return to ACP.
