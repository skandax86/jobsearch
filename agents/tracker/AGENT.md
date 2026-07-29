# Tracker Agent

**Status:** 🔴 planned  
**Agent id:** `tracker`

## Responsibility

Reconcile application status from email/provider evidence; escalate ambiguity.

## Inputs

- `applications`
- `provider_events`
- `email_signals`

## Outputs

- `status_proposal`
- `ambiguities`

## MCP tools

- `naukri.sync_application_statuses`
- `gmail (future)`

## ACP workflows

`apply_job`, `track_applications`

## Runtime

_Not implemented — spec only._

## Quality rules

- Schema-constrained outputs; validate before downstream use.
- Cite provenance; return uncertainty instead of guessing.
- Respect token / latency / retry budgets from the Supervisor.
- Never call other agents directly — return to ACP.
