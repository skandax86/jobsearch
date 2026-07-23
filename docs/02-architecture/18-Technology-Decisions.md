# Technology Decisions

**Document ID:** 02.18  
**Version:** 1.0  
**Status:** Draft  
**Last Updated:** 2026-07-12

---

## 1. Purpose

Summarize the initial technology choices for CareerPilot AI and the criteria for changing them. This document is an index of architectural decisions; durable rationale and changes must be recorded in the `adr/` directory.

## 2. Decision Principles

- Prefer managed, interoperable services for the MVP.
- Keep business logic and contracts independent from vendors.
- Choose mature tools with strong Python and TypeScript ecosystems.
- Optimize for safe delivery and operability before theoretical maximum scale.
- Replace technology only through a measured ADR, migration plan, and rollback plan.

## 3. Initial Stack

| Concern | Decision | Rationale | Review trigger |
|---|---|---|---|
| Web | Next.js + React + TypeScript | mature full-stack web framework, type safety, strong UI ecosystem | mobile/API-first requirements exceed web needs |
| API | Python FastAPI | async support, Pydantic validation, OpenAPI, AI ecosystem fit | service needs materially favor another runtime |
| Workflow/agents | LangGraph | stateful, durable graph-oriented agent workflows and approvals | workflow durability/scale requirements demand Temporal or equivalent |
| Agent coordination | ACP contracts over workflow state/event transport | explicit, testable agent messages and lifecycle | protocol interoperability requirement changes |
| Tool integrations | MCP clients and servers | standard tool/resource interfaces and integration isolation | provider lacks a safe MCP-compatible adapter |
| Relational data | PostgreSQL | ACID guarantees, ecosystem, managed-cloud support | measured scale or geographic constraints require sharding/distribution |
| Vectors | pgvector | co-locates embeddings with transactional data for MVP | recall, latency, or index scale proves inadequate |
| Cache/queues | Redis initially | simple cache, locks, rate limits, and worker broker | durable high-throughput streaming requires Pub/Sub, Kafka, or managed queues |
| Files | GCS behind a storage interface | managed, secure object storage and GCP alignment | customer/cloud portability requires S3/Azure implementation |
| Browser automation | Playwright | reliable modern browser control and isolated contexts | platform constraints or official API availability change approach |
| Containers | Docker | reproducible development and deployment units | none expected |
| Compute | Cloud Run first; GKE when operationally justified | fast managed deployment, then control/autoscaling for complex workers | long-running/browser workload or scale needs |
| IaC | Terraform | repeatable, reviewable multi-environment infrastructure | organization standard changes |
| Observability | OpenTelemetry + managed/compatible backends; LangSmith for AI traces | portable instrumentation plus AI-specific visibility | privacy, cost, or functionality gaps |
| CI/CD | GitHub Actions initially | repository-native automation and low setup cost | scale/security requirements justify dedicated platform tooling |

## 4. Interfaces That Must Remain Abstract

Business code depends on interfaces for LLM providers, embedding providers, object storage, queues/event buses, repositories, MCP tools, authentication, and notifications. Provider-specific clients live at integration boundaries.

## 5. Deferred Decisions

The following are deliberately deferred until there is evidence of need:

- dedicated vector database;
- Kafka or a full event-streaming platform;
- service mesh;
- multi-region active-active deployment;
- GraphQL/gRPC public APIs;
- native mobile applications;
- enterprise SSO and organization tenancy;
- self-hosted models and GPU inference.

## 6. ADR Process

Create an ADR for a material change to a listed decision, including context, options, decision, consequences, migration plan, owner, and status. Existing ADRs are indexed in `adr/`; this document must link to any newly accepted decision.

## 7. Related Documents

- [01-Architecture-Principles.md](01-Architecture-Principles.md)
- [04-Service-Architecture.md](04-Service-Architecture.md)
- [14-Cloud-Deployment.md](14-Cloud-Deployment.md)
- [19-Future-Architecture.md](19-Future-Architecture.md)
- [adr](adr)
