# CareerPilot AI

# Document 02.01 — Architecture Principles

**Version:** 1.0
**Status:** Draft
**Last Updated:** 2026-07-12

---

# 1. Purpose

This document defines the engineering principles that govern the architecture of CareerPilot AI.

These principles ensure that every component—whether built by human developers or AI coding agents—follows a consistent, scalable, secure, and maintainable design.

These principles are mandatory unless an Architecture Decision Record (ADR) explicitly documents an approved exception.

---

# 2. Goals

The architecture must:

* Scale horizontally.
* Support cloud-native deployment.
* Be AI-agent friendly.
* Enable rapid feature development.
* Support autonomous workflows.
* Be easy to test.
* Be easy to observe.
* Minimize coupling.
* Maximize modularity.
* Support long-term maintainability.

---

# 3. Architectural Philosophy

CareerPilot AI follows four primary architectural philosophies.

## 3.1 Domain-Driven Design (DDD)

The platform is organized around business domains rather than technical layers.

Primary domains include:

* Candidate
* Resume
* Job Discovery
* Applications
* Career Intelligence
* AI Platform
* Integrations
* Analytics
* Notifications

Each domain owns its business logic and data.

---

## 3.2 Cloud-Native First

Every component should assume cloud deployment from the beginning.

Design principles include:

* Stateless services
* Containerization
* Managed storage
* Autoscaling
* Infrastructure as Code
* Health checks
* Rolling deployments

The system should run locally while remaining cloud-compatible.

---

## 3.3 AI-Native

Artificial Intelligence is a platform capability—not an external add-on.

AI is responsible for:

* Resume understanding
* Semantic search
* Recommendation
* Resume optimization
* Interview coaching
* Career insights

Business workflows should seamlessly integrate AI where it adds measurable value.

---

## 3.4 Event-Driven

Long-running business operations communicate using events rather than synchronous service chains.

Examples:

* ResumeUploaded
* JobsDiscovered
* ResumeOptimized
* ApplicationSubmitted
* InterviewScheduled

This enables:

* Better scalability
* Retry support
* Loose coupling
* Independent processing

---

# 4. Layered Architecture

The system is divided into logical layers.

```text
Presentation Layer

↓

API Layer

↓

Business Services

↓

AI Platform

↓

Integration Layer (MCP)

↓

Data Layer

↓

Infrastructure
```

Each layer communicates only with adjacent layers.

Cross-layer shortcuts should be avoided.

---

# 5. Separation of Concerns

Every component must have one clearly defined responsibility.

Examples:

Resume Service

Responsible for:

* Resume storage
* Resume versions
* Resume metadata

Not responsible for:

* Job ranking
* Applications
* Notifications

---

Job Service

Responsible for:

* Job discovery
* Job normalization
* Job storage

Not responsible for:

* Resume optimization
* Email
* Authentication

---

# 6. Single Responsibility Principle

Each service, module, class, and AI agent should solve one problem.

Examples:

✔ Resume Agent

Analyze resumes only.

✔ Ranking Agent

Rank jobs only.

✔ Cover Letter Agent

Generate cover letters only.

Avoid multi-purpose agents.

---

# 7. API-First Development

Every internal capability must expose a documented interface.

No service should rely on another service's internal implementation.

Requirements:

* OpenAPI
* Versioned APIs
* Stable contracts
* Typed schemas

---

# 8. Contract-First Design

Every interface must be defined before implementation.

Examples:

REST APIs

ACP Messages

MCP Tools

Database Events

Webhook Payloads

Advantages:

* Parallel development
* Easier testing
* AI coding compatibility

---

# 9. Stateless Services

Business services must not depend on local memory.

Store persistent state in:

* PostgreSQL
* Redis
* Object Storage

Benefits:

* Horizontal scaling
* Easier deployments
* High availability

---

# 10. Asynchronous Processing

Long-running tasks should execute asynchronously.

Examples:

* Resume parsing
* Job crawling
* Resume optimization
* Embedding generation
* Cover letter generation
* Browser automation

Use queues and workers instead of blocking API requests.

---

# 11. ACP Principles

AI agents communicate only through ACP.

Agents should never invoke each other directly.

Every ACP message must include:

* Task ID
* Workflow ID
* Correlation ID
* Sender
* Receiver
* Status
* Payload
* Timestamp

Agents should be replaceable without affecting other agents.

---

# 12. MCP Principles

External systems should be accessed through MCP interfaces whenever practical.

Examples:

* Gmail
* Calendar
* GitHub
* Resume Storage
* Job Boards
* ATS Platforms

Benefits:

* Standardized interfaces
* Reduced vendor lock-in
* Easier testing
* Better security boundaries

---

# 13. AI Agent Principles

Every AI agent must:

* Have one responsibility.
* Define clear inputs.
* Produce structured outputs.
* Maintain deterministic interfaces.
* Be independently testable.
* Support retries.
* Report confidence where appropriate.
* Avoid modifying factual user data without approval.

---

# 14. Human-in-the-Loop

Critical actions require user approval unless autonomous mode has been explicitly enabled.

Examples requiring approval:

* Resume content changes
* Application submission
* Recruiter messages
* Email sending
* Calendar updates

Autonomous execution must remain configurable.

---

# 15. Data Principles

A resume should be parsed once into a canonical profile.

Downstream services consume structured data instead of repeatedly parsing documents.

Data should be:

* Normalized
* Versioned
* Auditable
* Immutable where appropriate

---

# 16. Versioning Principles

Version the following artifacts:

* APIs
* Prompts
* Resume templates
* AI models
* Agent workflows
* Configuration
* Database migrations

Avoid breaking changes whenever possible.

---

# 17. Security by Design

Security is part of the architecture—not an afterthought.

Requirements include:

* Encryption in transit
* Encryption at rest
* OAuth where supported
* Secret management
* Least privilege access
* Audit logs
* Secure session handling

Sensitive information must never appear in application logs.

---

# 18. Scalability Principles

The architecture should scale horizontally.

Preferred strategies:

* Stateless APIs
* Distributed workers
* Queue-based execution
* Managed databases
* Object storage
* Independent service scaling

Avoid assumptions that require a single server.

---

# 19. Reliability Principles

Services should degrade gracefully.

Requirements:

* Retries
* Timeouts
* Circuit breakers
* Health checks
* Dead-letter queues
* Idempotent operations

Critical workflows must recover from transient failures without data corruption.

---

# 20. Observability Principles

Every significant action should produce telemetry.

Capture:

* Logs
* Metrics
* Distributed traces
* Audit events
* AI execution history
* Prompt versions
* Tool usage
* Agent decisions

Operational visibility should be available without enabling debug mode.

---

# 21. Configuration Principles

Configuration belongs outside the application code.

Examples:

* LLM provider
* API endpoints
* Feature flags
* Queue settings
* Rate limits
* Supported job boards

Environment-specific behavior should be driven by configuration.

---

# 22. Documentation Principles

Documentation is treated as part of the codebase.

Requirements:

* Version controlled
* Peer reviewed
* Updated with implementation changes
* Linked to Architecture Decision Records (ADRs)

Every significant architectural change requires documentation updates.

---

# 23. Technology Independence

Business logic should not depend directly on specific vendors.

Examples:

Instead of:

OpenAIClient

Prefer:

LLMProvider Interface

Instead of:

PostgresRepository

Prefer:

Repository Interface

This allows future technology replacement with minimal business logic changes.

---

# 24. Coding Standards

Engineering expectations include:

* Type-safe interfaces
* Automated formatting
* Static analysis
* Unit testing
* Integration testing
* Clear naming conventions
* Small, focused modules
* Dependency injection where appropriate

Code should be understandable by both human developers and AI coding agents.

---

# 25. Acceptance Criteria

The architecture satisfies this document if:

* Components are modular and independently deployable.
* AI agents communicate only through ACP.
* External systems are accessed through MCP where practical.
* Services remain stateless.
* Long-running tasks execute asynchronously.
* Security and observability are built into every layer.
* New features can be added without major architectural redesign.

---

# 26. Related Documents

This document provides architectural rules for:

* High-Level Architecture
* Component Architecture
* Service Architecture
* AI Agent Architecture
* MCP Architecture
* ACP Architecture
* Database Design
* API Specification
* Security Architecture
* Cloud Deployment
* Observability
* Testing Strategy

All future engineering documents must comply with these principles.
