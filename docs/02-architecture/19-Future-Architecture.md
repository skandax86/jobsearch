# Future Architecture

**Document ID:** 02.19  
**Version:** 1.0  
**Status:** Draft  
**Last Updated:** 2026-07-12

---

## 1. Purpose

Describe the architectural direction beyond the initial public SaaS release. This is a guardrail for extension, not a commitment to build every capability or a substitute for product validation and ADRs.

## 2. Principles

- Evolve from measured user and operational needs, not speculative complexity.
- Preserve user control, truthfulness, and explicit approval for high-impact actions.
- Maintain domain contracts while extracting services or adding providers.
- Make enterprise isolation and compliance additive rather than a rewrite.

## 3. Evolution Stages

### Stage 1 — Assisted MVP

Next.js, FastAPI, PostgreSQL/pgvector, Redis, object storage, LangGraph, and human-approved workflows. Deploy managed services on GCP/Cloud Run or a small GKE footprint. Focus on resume intelligence, job discovery, ranking, and tracking.

### Stage 2 — Public SaaS

Introduce plan quotas, durable workflow operations, production observability, formal data-retention controls, browser-worker isolation, provider rate limits, and CI/CD/IaC. Continue with a modular monolith plus specialized workers where possible.

### Stage 3 — Scale and Intelligence

Add a dedicated analytics plane, experimentation/evaluation pipelines, richer company and market intelligence, recommendation feedback loops, and selectively extracted services for proven bottlenecks such as job ingestion, notifications, or browser automation.

### Stage 4 — Enterprise and Organizations

Add organization/tenant boundaries, RBAC extensions, SSO/SAML, SCIM, tenant-aware audit and retention policies, data residency options, and private integration configurations. Evaluate per-tenant encryption and isolated deployments for regulated customers.

### Stage 5 — Ecosystem

Offer documented APIs, webhooks, an integration marketplace, partner-managed MCP servers, workflow templates, and governed extension points. Third-party agents and tools require capability-scoped permissions, sandboxing, review, and auditability.

## 4. Future Reference Architecture

```text
Clients and partner applications
             │
 API / webhook / extension gateway
             │
 Domain services and workflow control plane
        ┌────┴────┐
  agent runtime  integration/MCP platform
        │              │
 analytics/evaluation  provider adapters
        │              │
 operational, vector, object, and analytical data planes
```

The control plane manages identity, tenant policy, workflow definitions, quotas, configuration, audit, and observability. The data plane processes tenant requests and stores tenant data. This separation becomes important only when organization support and extension ecosystems are real requirements.

## 5. Candidate Future Capabilities

- Career-market intelligence using aggregated, privacy-preserving data.
- Interview and learning workflows with explicit user review.
- Referral and networking CRM, subject to integration policy and consent.
- Multimodal resume/portfolio understanding.
- Model routing by cost, latency, quality, and data residency.
- Regional failover, data residency, and customer-managed keys.
- A dedicated warehouse/lakehouse for analytics and evaluation datasets.

## 6. Architectural Triggers

| Observation | Evaluate |
|---|---|
| sustained queue backlog or worker interference | dedicated worker services / autoscaling changes |
| PostgreSQL or pgvector measured limits | read replicas, partitioning, dedicated vector service |
| complex long-running workflow requirements | durable workflow engine evaluation |
| repeated provider outages/rate limits | multi-provider routing and stronger integration isolation |
| enterprise contracts | SSO, tenancy, audit, residency, isolated deployments |
| analytics impacts production workloads | warehouse/lakehouse and event pipeline |

## 7. Non-Negotiable Guardrails

Future autonomy must not bypass consent, fabricate candidate information, obscure model or tool actions, or weaken auditability. All extensions preserve least privilege, human escalation paths, and domain ownership.

## 8. Governance

Each stage transition requires product validation, security review, capacity/cost analysis, migration and rollback plans, and ADR approval. Roadmap items remain optional until these conditions are met.

## 9. Related Documents

- [00-Overview.md](00-Overview.md)
- [01-Architecture-Principles.md](01-Architecture-Principles.md)
- [15-Scalability.md](15-Scalability.md)
- [16-Failure-Recovery.md](16-Failure-Recovery.md)
- [18-Technology-Decisions.md](18-Technology-Decisions.md)
