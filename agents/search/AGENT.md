# Search / Job Discovery Agent

**Status:** 🟡 partial  
**Agent id:** `search`

## Responsibility

Find and normalize job postings from configured providers (Remotive, Naukri, demo; LinkedIn via Cursor MCP).

## Inputs

- `query`
- `location`
- `filters`
- `provider_flags`

## Outputs

- `job_postings`
- `provider_stats`

## MCP tools

- `naukri.search_jobs`
- `linkedin.search_jobs (Cursor)`

## ACP workflows

`job_discovery`

## Runtime

apps/api/src/careerpilot/agents/job_discovery.py

## Quality rules

- Schema-constrained outputs; validate before downstream use.
- Cite provenance; return uncertainty instead of guessing.
- Respect token / latency / retry budgets from the Supervisor.
- Never call other agents directly — return to ACP.
