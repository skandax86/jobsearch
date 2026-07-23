# Scalability Architecture

**Document ID:** 02.15  
**Version:** 1.0  
**Status:** Draft  
**Last Updated:** 2026-07-12

---

## 1. Purpose

Define how CareerPilot AI scales safely from local development and an MVP to a multi-tenant public SaaS. This document covers capacity, isolation, autoscaling, and cost controls; it does not replace the deployment design in [14-Cloud-Deployment.md](14-Cloud-Deployment.md).

## 2. Goals

- Keep interactive API requests responsive under variable demand.
- Scale API, AI, job-discovery, and browser workloads independently.
- Protect shared services from noisy tenants and provider limits.
- Preserve correctness during concurrent and repeated work.
- Make scale decisions observable and cost-aware.

## 3. Principles

- Prefer stateless services and horizontal replication.
- Queue all long-running work; never hold an HTTP request open for an agent workflow.
- Apply backpressure before a dependency becomes unhealthy.
- Use idempotency keys for side-effecting operations.
- Partition by workload class and, where relevant, tenant.
- Start managed and simple; introduce additional distributed systems only when measured load requires them.

## 4. Scaling Model

```text
Client traffic ──> Web/API replicas ──> Queue / event bus ──> specialized workers
                                              │
                         PostgreSQL + pgvector │ Redis │ Object storage │ MCP providers
```

The API accepts, validates, persists intent, and enqueues work. Workers consume independently. The ACP orchestrator persists workflow state so replicas can continue work after restarts.

## 5. Workload Classes

| Class | Examples | Primary scale signal | Isolation |
|---|---|---|---|
| Interactive | dashboard, search filters, approvals | p95 latency, CPU | web/API replicas |
| CPU | parsing, normalization, analytics | queue depth, CPU | CPU worker pool |
| AI | LangGraph runs, generation, embeddings | queue age, provider rate limits | AI worker pool |
| Browser | Playwright and ATS flows | active sessions, queue age | isolated browser pool |
| Scheduled | refreshes, cleanup, summaries | schedule lag | scheduler/worker pool |

Browser workers must never share a pool with API or AI workers. Their concurrency is capped per provider, user, and account.

## 6. Service and Worker Scaling

- **Web/API:** scale on CPU, memory, request concurrency, and p95 latency. Keep instances stateless.
- **ACP orchestrator:** scale consumers by queued workflow count; use workflow and idempotency locks to prevent duplicate execution.
- **Workers:** use queue-specific autoscaling with minimum warm capacity for latency-sensitive jobs.
- **MCP services:** scale independently and use per-provider concurrency limits, timeouts, and circuit breakers.
- **Playwright:** one isolated browser context per job; recycle workers after a configurable number of sessions.

For GKE, use HPA/KEDA driven by CPU and queue metrics. For Cloud Run, use request concurrency for API services and a queue-triggered worker pattern where supported.

## 7. Data Scaling

### PostgreSQL and pgvector

- Use indexes, pagination, and bounded queries first.
- Use connection pooling; application replicas must not create unbounded database connections.
- Add read replicas for read-heavy dashboard and reporting queries only after profiling.
- Partition large, append-heavy tables such as audit events, agent executions, and analytics events by time.
- Keep transactional records and vector indexes in PostgreSQL initially. Evaluate a dedicated vector store only when pgvector latency, index size, or operational constraints are measured bottlenecks.

### Redis and object storage

- Redis holds cache, locks, rate-limit counters, and ephemeral queues; it is not the source of truth.
- Use TTLs, key namespaces, and memory eviction policies.
- Store files in cloud object storage with lifecycle rules, checksums, and signed URLs. Object storage scales independently from compute.

## 8. Tenant and Provider Protection

- Enforce per-user and plan-based quotas for AI runs, searches, uploads, and application attempts.
- Enforce provider-specific budgets and rate limits in MCP adapters.
- Use fair queues or tenant-aware concurrency to prevent one tenant from monopolizing workers.
- Apply maximum workflow duration, token budget, tool-call budget, and browser-session budget.

## 9. Backpressure and Load Shedding

When capacity is constrained:

1. Reject or defer non-critical scheduled work.
2. Queue new asynchronous work and show its status to the user.
3. Reduce optional enrichment and expensive model calls.
4. Apply endpoint- and tenant-level rate limits.
5. Open dependency circuit breakers when error thresholds are exceeded.

The system must never silently drop user-approved applications or durable domain events.

## 10. Capacity Management

Maintain per-environment targets for API latency, workflow queue age, worker utilization, database saturation, provider quota consumption, and monthly AI spend. Load-test the resume-upload, job-search, and application-approval paths before public launch and before major capacity changes.

## 11. Cost Controls

- Route simple classification/extraction tasks to lower-cost models when quality evaluation permits.
- Cache deterministic or safely reusable results with explicit expiry and user-data boundaries.
- Batch embeddings and analytics.
- Use autoscaling and scale-to-zero only for workloads that tolerate cold starts.
- Set budget alerts for model providers, browser compute, managed databases, and egress.

## 12. Operational Guidance

- Define SLOs and capacity thresholds in [17-Observability.md](17-Observability.md).
- Treat sustained queue age, database connection saturation, and provider 429s as scale signals.
- Rehearse a scale-out scenario and a provider-throttling scenario at least once per release cycle.
- Record material scaling decisions in an ADR.

## 13. Future Evolution

Potential later steps include regional deployment, tenant-aware data partitioning, dedicated analytics storage, dedicated vector infrastructure, and Kubernetes cluster autoscaling. Adopt these only after workload measurements justify their operational cost.

## 14. Related Documents

- [04-Service-Architecture.md](04-Service-Architecture.md)
- [08-Event-Driven-Architecture.md](08-Event-Driven-Architecture.md)
- [09-Data-Layer.md](09-Data-Layer.md)
- [11-Worker-Architecture.md](11-Worker-Architecture.md)
- [14-Cloud-Deployment.md](14-Cloud-Deployment.md)
- [16-Failure-Recovery.md](16-Failure-Recovery.md)
