# Domain Model Overview

**Document ID:** 03.00  
**Version:** 1.0  
**Status:** Draft  
**Last Updated:** 2026-07-12

---

## 1. Purpose

This document defines the business-domain boundaries of CareerPilot AI. It is the source of truth for domain language, data ownership, aggregate boundaries, and cross-domain collaboration.

The domain model drives the database schema, API contracts, service boundaries, ACP workflows, and agent responsibilities. It does not prescribe implementation classes or table definitions.

## 2. Goals

- Create a shared, unambiguous vocabulary for humans and AI coding agents.
- Keep business rules close to the domain that owns them.
- Prevent shared mutable data and cross-domain database writes.
- Support an MVP as a modular monolith while allowing later service extraction.
- Preserve truthfulness, user consent, traceability, and tenant isolation.

## 3. Domain Principles

### Ubiquitous language

The terms in this document are used consistently in code, APIs, events, prompts, and user interfaces. Do not use `user`, `candidate`, `resume`, and `profile` interchangeably when they represent distinct concepts.

### Bounded contexts

Each domain owns its rules and write model. Other domains interact through published contracts, domain events, or approved service APIs—not direct table access.

### Source of truth

PostgreSQL is the operational source of truth for business state. Object storage holds immutable document objects. pgvector holds derived semantic indexes. Redis holds ephemeral cache, locks, and queues.

### Truth and consent

User-provided facts are canonical until changed by the user. AI-generated suggestions never become factual candidate data without explicit user confirmation. Any external side effect, such as a submitted application or sent message, must be auditable.

## 4. Core Domain Map

```text
Identity & Access
       │
       ▼
Candidate ─── Resume ───┐
       │                │
       ▼                ▼
Career Intelligence   Job Discovery ─── Company
       │                     │
       └──────────┬──────────┘
                  ▼
             Application ─── Interview
                  │
                  ▼
          Notifications & Communications

AI Platform, ACP, MCP, Analytics, and Integrations are supporting domains.
```

## 5. Bounded Contexts

| Context | Responsibility | Primary aggregates | Owns writes to |
|---|---|---|---|
| Identity & Access | account identity, roles, consent, connected accounts | User, Session, Consent | identity and access data |
| Candidate | professional profile and job preferences | CandidateProfile, PreferenceSet | candidate facts and preferences |
| Resume | source documents, canonical content, versions, tailored variants, templates, and renders | Resume, ResumeVersion, ResumeRender | resume metadata, canonical content, and render provenance |
| Job Discovery | ingestion, normalization, deduplication, company linkage | JobPosting, JobSource | job and source records |
| Company | normalized company identity and enrichment | Company | company records |
| Matching & Career Intelligence | derived match results, gaps, recommendations | JobMatch, SkillGap, CareerRecommendation | derived recommendations only |
| Applications | preparation, approval, submission, lifecycle tracking | Application, ApplicationPackage | application state and evidence |
| Interviews | interview events and preparation artifacts | Interview | interview state and preparation records |
| Communications & Notifications | user notifications and approved outreach records | Notification, Conversation | delivery and communication records |
| AI Platform | agent runs, prompt/model metadata, evaluation evidence | AgentExecution | AI execution metadata |
| Integrations | provider connections, scopes, synchronization state | IntegrationConnection | encrypted connection metadata |
| Analytics | product and operational measures | AnalyticsEvent | derived analytics data |

## 6. Key Domain Terms

| Term | Definition |
|---|---|
| User | authenticated account holder who controls data and integrations. |
| Candidate | a user's professional identity used for job search; one user may initially own one candidate profile. |
| Candidate Profile | canonical, structured representation of verified professional facts and preferences. |
| Resume | a logical resume artifact containing immutable content versions and rendered outputs. |
| Resume Version | a source or generated content snapshot, with structured JSON and provenance. |
| Resume Render | an immutable PDF, DOCX, or HTML artifact produced from a content version, template, and renderer version. |
| Job Posting | a normalized representation of a role from one provider or company career site. |
| Job Source | provider-specific observation of a job posting, including source URL and retrieval time. |
| Job Match | derived, versioned assessment between a candidate profile/resume version and a job posting. |
| Application Package | the selected resume, cover letter, answers, and evidence prepared for one application. |
| Application | a candidate's attempt to apply to a job posting; it is distinct from a saved job. |
| Approval | explicit user authorization to perform a configured high-impact action. |
| Workflow | durable ACP execution coordinating tasks to reach a business outcome. |
| Integration Connection | a user-authorized link to an external provider with scoped credentials stored outside domain records. |

## 7. Aggregate Boundaries

An aggregate is the smallest consistency boundary for a business write. Initial aggregate roots are:

- `User` for account and consent decisions.
- `CandidateProfile` for verified profile facts and preferences.
- `Resume` for resume-version lifecycle and source provenance.
- `JobPosting` for normalized job state and deduplication identity.
- `Company` for canonical organization identity.
- `Application` for approval, submission, and lifecycle transitions.
- `Interview` for scheduling and preparation lifecycle.
- `IntegrationConnection` for provider connection state.

Cross-aggregate changes are coordinated with domain events or ACP workflows. They must not use distributed database transactions.

## 8. Ownership and Collaboration Rules

1. Only the owning domain writes its aggregate records.
2. A domain publishes immutable events after a successful state change using the outbox pattern.
3. Consumers store only the data they need, with provenance and refresh rules.
4. Derived AI output is never treated as verified candidate fact unless approved.
5. Job sources may be merged into one job posting, but source observations remain traceable.
6. An application references immutable snapshots of the job, resume, and generated materials used at submission time.
7. Integration tokens, cookies, and secrets are not part of the general domain model; they remain in the security/integration boundary.

## 9. Domain Events

Initial domain events use past-tense names and the common schema defined in [02-architecture/08-Event-Driven-Architecture.md](../02-architecture/08-Event-Driven-Architecture.md).

| Owning domain | Representative events |
|---|---|
| Candidate | `CandidateProfileUpdated`, `PreferencesUpdated` |
| Resume | `ResumeUploaded`, `ResumeParsed`, `ResumeVersionCreated` |
| Job Discovery | `JobDiscovered`, `JobNormalized`, `JobDeduplicated` |
| Matching | `JobMatched`, `SkillGapIdentified` |
| Applications | `ApplicationPrepared`, `ApplicationApproved`, `ApplicationSubmitted`, `ApplicationStatusUpdated` |
| Interviews | `InterviewScheduled`, `InterviewPreparationGenerated` |
| Integrations | `IntegrationConnected`, `IntegrationConnectionExpired` |

Events carry opaque identifiers and minimum necessary data. Consumers fetch authorized details through domain APIs rather than copying sensitive payloads into the event stream.

## 10. State and Lifecycle Boundaries

The detailed state machines belong to their respective domain documents. At a high level:

```text
Resume: uploaded → parsed → verified → active → archived
Job: discovered → normalized → eligible/ineligible → expired
Application: draft → prepared → awaiting_approval → submitted → outcome
Interview: detected → scheduled → prepared → completed/cancelled
```

State transitions must validate ownership, current state, consent, and idempotency.

## 11. Multi-Tenancy and Privacy

The initial product is user-scoped. Every user-owned aggregate includes an ownership boundary and is filtered by authorization at the service layer. Future organization tenancy must add a `tenant_id` boundary without weakening user consent or data isolation.

Personal data minimization, retention, export, deletion, and audit obligations are defined by [02-architecture/13-Security-Architecture.md](../02-architecture/13-Security-Architecture.md) and the future security/privacy documentation.

## 12. Implementation Guidance

- Use domain-oriented modules rather than a single shared "models" package for business rules.
- Define typed commands, events, and read models at domain boundaries.
- Keep repositories scoped to aggregate roots.
- Store provenance for extracted and generated data: source, agent/model/prompt version when applicable, timestamp, and approval status.
- Do not allow AI agents to write business records directly; they return structured proposals for domain services or ACP workflows to validate and persist.

## 13. Domain Documentation Roadmap

The following documents expand this overview in order:

1. Candidate Domain
2. Resume Domain
3. Job and Company Domain
4. Application and Interview Domain
5. Career Intelligence Domain
6. AI Platform and Integration Domain

## 14. Related Documents

- [01-Product-Requirements-Document.md](../01-product/01-Product-Requirements-Document.md)
- [03-Component-Architecture.md](../02-architecture/03-Component-Architecture.md)
- [04-Service-Architecture.md](../02-architecture/04-Service-Architecture.md)
- [06-ACP-Architecture.md](../02-architecture/06-ACP-Architecture.md)
- [08-Event-Driven-Architecture.md](../02-architecture/08-Event-Driven-Architecture.md)
- [09-Data-Layer.md](../02-architecture/09-Data-Layer.md)
