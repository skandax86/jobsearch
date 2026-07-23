# Operations and Observability

**Document ID:** 13.00  
**Status:** Draft

## Purpose

Defines production telemetry, SLOs, dashboards, alerting, and incident operations. Architecture-level telemetry requirements are defined in [17-Observability.md](../02-architecture/17-Observability.md).

## Required Signals

Instrument web/API requests, queue age and DLQ depth, workflow state transitions, agent model/prompt/token/cost metrics, MCP provider latency/errors/rate limits, Playwright session outcomes, database health, storage failures, and security events.

OpenTelemetry carries traces, logs, and metrics. Propagate request, correlation, workflow, and safe actor identifiers. Never use PII or secret values as metric labels or log fields.

## SLO Operations

Define and review availability, API latency, workflow acceptance, queue age, and user-approved application outcome SLOs. Alerts must be actionable, severity-tagged, owned, linked to a dashboard/runbook, and tuned to avoid noise.

## Incident Workflow

`detect → triage → contain unsafe automation → mitigate → recover → reconcile → communicate → postmortem`.

Postmortems are blameless and create tracked follow-up work for code, tests, runbooks, or architecture.

## Related Documents

- [16-Failure-Recovery.md](../02-architecture/16-Failure-Recovery.md)
- [00-Deployment-and-Infrastructure.md](../11-deployment/00-Deployment-and-Infrastructure.md)
