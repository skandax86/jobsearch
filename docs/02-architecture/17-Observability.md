# Observability Architecture

**Document ID:** 02.17  
**Version:** 1.0  
**Status:** Draft  
**Last Updated:** 2026-07-12

---

## 1. Purpose

Define the telemetry, operational visibility, alerting, and audit requirements for CareerPilot AI. Observability must make it possible to answer: what happened, to whom, why, where it failed, how much it cost, and whether it is safe to retry.

## 2. Goals

- Diagnose failures across API, ACP, agent, MCP, worker, and browser boundaries.
- Measure user experience, platform reliability, capacity, and AI quality/cost.
- Maintain privacy-aware auditability for sensitive actions.
- Provide actionable alerts rather than noisy telemetry.

## 3. Principles

- Emit structured logs, metrics, and traces from every deployable unit.
- Propagate `request_id`, `correlation_id`, `workflow_id`, `user_id` (where permitted), and `tenant_id` (future) across all boundaries.
- Treat personal data, credentials, prompts, and documents as sensitive; redact by default.
- Instrument code at the boundary of every remote call and state transition.
- Separate operational telemetry from immutable security/business audit events.

## 4. Architecture

```text
Web / API / workers / ACP / MCP / browser
                    │
             OpenTelemetry SDKs
                    │
      logs ─────> log backend
      metrics ───> Prometheus / managed metrics ──> Grafana
      traces ────> Tempo, Jaeger, or managed tracing
      AI traces ─> LangSmith or equivalent (redacted)
      audits ────> PostgreSQL / immutable audit sink
```

OpenTelemetry is the vendor-neutral instrumentation standard. The concrete backend may vary by environment; exporters must be configuration-driven.

## 5. Telemetry Standards

### Logs

Use JSON logs with timestamp, severity, service, deployment version, trace ID, correlation ID, event name, and safe error code. Do not log resume contents, OAuth tokens, cookies, API keys, full prompts, or raw provider responses unless an approved redaction policy permits it.

### Metrics

Use counters, histograms, and gauges. Metric names are namespaced by service and avoid high-cardinality labels such as raw user IDs, job titles, or URLs.

### Traces

Create spans for inbound requests, database calls, queue publish/consume, ACP transitions, agent invocations, LLM calls, MCP tool calls, and browser runs. Link async spans with trace context and correlation IDs.

### Audit events

Audit login, consent, integration connection, resume mutation, generated-content approval, application submission, and privileged operations. Audit records require actor, action, target, timestamp, outcome, and correlation ID.

## 6. Required Service Metrics

| Area | Required signals |
|---|---|
| Web/API | request rate, p50/p95/p99 latency, 4xx/5xx rate, rate-limit rejections |
| Workers | queue depth, queue age, throughput, active jobs, retries, DLQ count |
| PostgreSQL | connection usage, query latency, errors, replication/backup health |
| Redis | memory, evictions, command latency, availability |
| Object storage | upload/download failure rate, latency, lifecycle failures |
| Browser | active sessions, form completion rate, crash rate, ambiguous outcomes |
| MCP | tool latency, provider errors, 429s, OAuth refresh failures |
| ACP | workflow duration, state transitions, approval wait time, completion/failure rate |

## 7. AI Observability

For each agent execution, record the agent/version, workflow and task IDs, model/provider, prompt version, structured-output validation result, tool calls, latency, input/output token counts, estimated cost, confidence, retry count, and outcome.

Prompt and output content must be sampled or redacted under a documented privacy policy. AI quality measures (such as schema-valid rate, user acceptance rate, and hallucination findings) belong in evaluation dashboards, not only logs.

## 8. Dashboards

Minimum production dashboards:

1. **Executive health:** availability, active users, major workflow success rate, spend.
2. **API and web:** latency, errors, saturation, deployment comparison.
3. **Workflows:** ACP state distribution, queue age, retries, DLQ.
4. **Integrations:** MCP provider status, rate limits, browser outcomes.
5. **Data:** PostgreSQL, Redis, object storage, backup status.
6. **AI:** agent latency, validation failure, provider error, token/cost trends.
7. **Security:** failed login, authorization denial, unusual privileged actions.

## 9. Alerting

Page only for actionable, user-impacting conditions: sustained API errors, unavailable primary database, workflow backlog beyond SLO, failed backups, security incidents, or automated-application ambiguity above threshold. Route lower-severity warnings to an operations channel and create tickets for recurring issues.

Every alert must include an owner, severity, runbook link, dashboard link, and correlation scope.

## 10. SLOs and Error Budgets

Initial SLO candidates:

- API availability: 99.9% monthly, excluding planned maintenance.
- Read API p95 latency: under 500 ms where no asynchronous work is started.
- Durable workflow acceptance: 99.9% successful persistence before acknowledgement.
- User-approved application workflow: track success and ambiguous-outcome rates separately; do not hide ambiguity in a single success metric.

SLOs are product commitments and must be revised with measured traffic and provider constraints.

## 11. Retention and Access

Set environment-specific retention for logs, traces, metrics, and audits. Limit production telemetry access by role, redact sensitive fields, and support deletion/anonymization workflows where legal requirements apply.

## 12. Operational Guidance

- Add telemetry as part of every new API, agent, workflow, MCP tool, and queue consumer.
- Verify trace propagation in integration tests.
- Review dashboards and alert thresholds after major releases.
- Link incidents and postmortems to the relevant traces, audit entries, and runbooks.

## 13. Related Documents

- [06-ACP-Architecture.md](06-ACP-Architecture.md)
- [07-MCP-Architecture.md](07-MCP-Architecture.md)
- [11-Worker-Architecture.md](11-Worker-Architecture.md)
- [13-Security-Architecture.md](13-Security-Architecture.md)
- [15-Scalability.md](15-Scalability.md)
- [16-Failure-Recovery.md](16-Failure-Recovery.md)
