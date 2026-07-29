# Recruiter Outreach Agent

**Status:** 🔴 planned  
**Agent id:** `recruiter`

## Responsibility

Draft recruiter outreach / networking messages from verified profile (send requires approval).

## Inputs

- `profile`
- `target_person_or_company`

## Outputs

- `draft_message`

## MCP tools

- `linkedin (Cursor)`

## ACP workflows

_(none yet)_

## Runtime

_Not implemented — spec only._

## Quality rules

- Schema-constrained outputs; validate before downstream use.
- Cite provenance; return uncertainty instead of guessing.
- Respect token / latency / retry budgets from the Supervisor.
- Never call other agents directly — return to ACP.
