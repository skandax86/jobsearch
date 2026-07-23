# Failure Recovery Architecture

**Document ID:** 02.16  
**Version:** 1.0  
**Status:** Draft  
**Last Updated:** 2026-07-12

---

## 1. Purpose

Define how CareerPilot AI detects, contains, recovers from, and learns from failures across APIs, workflows, integrations, data stores, and infrastructure.

## 2. Goals

- Prevent duplicate side effects, especially applications and messages.
- Recover transient failures automatically where safe.
- Preserve durable user intent and workflow state.
- Provide clear, actionable status to users and operators.
- Meet recovery objectives appropriate to a public SaaS.

## 3. Principles

- Fail closed for authorization and sensitive actions.
- Use timeouts on every remote dependency.
- Retry only transient, idempotent, or explicitly idempotency-protected operations.
- Isolate failing dependencies with circuit breakers and bulkheads.
- Persist state before emitting side effects; use an outbox pattern for reliable event publication.
- Prefer compensation and reconciliation over distributed transactions.

## 4. Failure Model

| Failure class | Examples | Default response |
|---|---|---|
| Validation | malformed resume, invalid state transition | fail immediately; return actionable error |
| Authorization | expired OAuth, insufficient permission | stop; request reconnection or approval |
| Transient dependency | timeout, 429, 503 | bounded retry with backoff and jitter |
| Permanent provider | unsupported form, removed job | mark task failed; retain evidence |
| Worker/infrastructure | pod crash, deploy interruption | resume from persisted workflow state |
| Data | database outage, corruption risk | fail safe; restore/reconcile from backups |

## 5. Recovery Architecture

```text
Request / event
      │
validation → idempotency check → durable state / outbox → worker execution
                                                   │
                                 success <─────────┼─────────> retry queue → DLQ
                                                   │
                                           audit + trace + user status
```

## 6. Idempotency and State

Every command that creates an external or user-visible side effect requires an idempotency key. Application submission keys must combine at least the user, normalized job identity, resume version, and submission attempt. Persist attempt state before invoking an MCP tool or browser worker.

Required states include `queued`, `running`, `waiting_for_approval`, `succeeded`, `retry_scheduled`, `failed`, `cancelled`, and `manual_review`. State transitions are validated and audited.

## 7. Retries, Timeouts, and DLQs

- Use short connection and request timeouts; do not rely on provider defaults.
- Retry transient failures with exponential backoff and jitter, bounded by a per-task retry budget.
- Do not retry invalid input, denied access, user cancellation, or an already-completed idempotent operation.
- Send exhausted work to a dead-letter queue with failure class, safe diagnostic metadata, and replay instructions.
- DLQ replay requires an operator or automated reconciliation rule; replay must retain the original idempotency key.

## 8. Dependency-Specific Recovery

### PostgreSQL

Use managed backups and point-in-time recovery. During an outage, reject writes that cannot be durably accepted and degrade read-only functions only if a safe replica is available. Reconcile queued work after recovery.

### Redis / queue broker

Treat Redis as ephemeral. Durable business state remains in PostgreSQL. Rebuild cache and safely re-enqueue work from workflow records or the outbox after recovery.

### LLM providers

Use provider timeouts, bounded retries, and model/provider fallback only for tasks whose quality and data-handling policies permit it. Never silently substitute a model for high-impact content generation without recording the model used.

### MCP providers and browser automation

Pause workflows on OAuth expiration, CAPTCHA, unsupported forms, or ambiguous submission outcome. For uncertain submission outcomes, reconcile by inspecting a confirmation page, provider record, or user-visible evidence before retrying. Never re-submit merely because a browser session crashed.

## 9. Human Recovery Paths

Require human review for:

- ambiguous application submission status;
- conflicting candidate facts or generated resume edits;
- repeated provider failures;
- exhausted retry budget on user-approved work;
- suspected account or credential compromise.

The UI must show the failed step, next safe action, and any non-sensitive diagnostic reference.

## 10. Data Protection and Objectives

Initial production targets:

| Asset | RPO | RTO |
|---|---:|---:|
| PostgreSQL primary data | ≤ 15 minutes | ≤ 4 hours |
| Object storage documents | ≤ 24 hours, preferably versioned | ≤ 4 hours |
| Redis cache/ephemeral queues | best effort | ≤ 1 hour |
| Logs and traces | best effort | ≤ 24 hours |

Targets must be reviewed before each production tier change. Backup restoration and workflow-recovery exercises are required at least quarterly.

## 11. Incident Operations

1. Detect via alert, health check, or user report.
2. Triage severity and contain unsafe automation.
3. Preserve traces, audit evidence, and affected workflow IDs.
4. Recover service/data, reconcile side effects, and communicate status.
5. Complete a blameless post-incident review with corrective actions.

## 12. Related Documents

- [06-ACP-Architecture.md](06-ACP-Architecture.md)
- [07-MCP-Architecture.md](07-MCP-Architecture.md)
- [08-Event-Driven-Architecture.md](08-Event-Driven-Architecture.md)
- [11-Worker-Architecture.md](11-Worker-Architecture.md)
- [13-Security-Architecture.md](13-Security-Architecture.md)
- [17-Observability.md](17-Observability.md)
