# CareerPilot AI

# Document 02 — System Architecture

## 00. Overview

**Version:** 1.0
**Status:** Draft
**Last Updated:** 2026-07-12

---

# 1. Purpose

This document defines the complete technical architecture of CareerPilot AI.

It serves as the primary engineering blueprint for implementing, deploying, operating, and scaling the platform.

Unlike the Product Requirements Document (PRD), which focuses on business requirements, this document defines **how the platform is engineered**.

All future engineering decisions—including APIs, database schemas, AI agents, ACP workflows, MCP integrations, infrastructure, and deployment—must align with this architecture.

---

# 2. Scope

This document covers the architecture for:

* Web Application
* Backend Services
* AI Agent Platform
* ACP Orchestration Layer
* MCP Integration Layer
* Resume Intelligence
* Job Discovery
* Application Automation
* Analytics
* Infrastructure
* Cloud Deployment
* Observability
* Security
* Scalability

This document intentionally does **not** define:

* Detailed database schemas
* API contracts
* Individual AI agent specifications
* Prompt engineering
* Infrastructure provisioning scripts

These are specified in dedicated design documents.

---

# 3. Architectural Vision

CareerPilot AI is designed as an **AI-native, cloud-native, event-driven Career Operating System**.

The platform combines modern software architecture with autonomous AI agents to create a scalable and extensible ecosystem for career management.

Unlike traditional web applications where business logic resides entirely inside backend services, CareerPilot AI distributes intelligent decision-making across specialized AI agents coordinated through ACP while accessing external tools and data through MCP.

The architecture prioritizes:

* Modularity
* Scalability
* Reliability
* Explainability
* Security
* Extensibility

---

# 4. High-Level Goals

The architecture is designed to achieve the following objectives.

## Functional Goals

Support:

* Resume Intelligence
* Job Discovery
* Job Matching
* Resume Optimization
* Cover Letter Generation
* Human-approved Applications
* Autonomous Application Workflows
* Interview Preparation
* Career Intelligence
* Recruiter Assistance
* Application Tracking

---

## Technical Goals

Provide:

* Stateless services
* Horizontal scalability
* Multi-agent orchestration
* Event-driven workflows
* Modular services
* Cloud-native deployment
* High observability
* Fault tolerance
* Vendor flexibility
* AI model abstraction

---

## Business Goals

Enable:

* SaaS deployment
* Multi-user support
* Subscription plans
* Enterprise readiness
* Continuous feature expansion
* Regional cloud deployments
* International job support

---

# 5. Architectural Style

CareerPilot AI combines multiple architectural styles.

## Cloud-Native Architecture

All platform services are designed to run inside containers and be deployable on Kubernetes or managed cloud platforms.

Characteristics:

* Stateless APIs
* Managed databases
* Managed object storage
* Auto scaling
* Rolling deployments

---

## Event-Driven Architecture

Long-running workflows communicate through asynchronous events.

Examples:

* Resume uploaded
* Jobs discovered
* Resume optimized
* Application submitted
* Interview scheduled

Benefits:

* Loose coupling
* Better scalability
* Retry support
* Independent processing

---

## Multi-Agent Architecture

AI capabilities are implemented as specialized agents rather than a single monolithic AI service.

Each agent owns one responsibility.

Examples:

* Resume Agent
* Search Agent
* Ranking Agent
* Resume Optimizer
* Cover Letter Agent
* Application Agent
* Interview Coach

---

## Service-Oriented Architecture

Business capabilities are implemented as independent services with clearly defined responsibilities.

Examples:

* Authentication
* Resume Service
* Job Service
* Application Service
* Notification Service
* Analytics Service

---

# 6. Architectural Principles

The architecture follows these principles.

## Separation of Concerns

Each layer has a single responsibility.

UI should never contain business logic.

Agents should never manage persistence directly.

Infrastructure should remain independent of business logic.

---

## Loose Coupling

Components communicate through APIs, ACP messages, or events.

Direct dependencies between unrelated components should be avoided.

---

## High Cohesion

Each service should focus on one domain.

Examples:

Resume Service manages resumes only.

Job Service manages jobs only.

Notification Service manages notifications only.

---

## Cloud First

The system assumes deployment to cloud infrastructure from the beginning.

Local development should emulate cloud behavior where practical.

---

## API First

Every internal capability should be accessible through well-defined interfaces.

Services should not rely on undocumented internal behavior.

---

## AI First

Artificial intelligence is treated as a first-class platform capability.

AI services are integrated into business workflows rather than isolated as optional enhancements.

---

## Human First

AI augments user decision-making.

Critical actions should require explicit user approval unless autonomous mode has been enabled.

---

# 7. System Context

The platform interacts with multiple categories of systems.

## Client Applications

* Web Dashboard
* Future Mobile Application
* Browser Extension
* Public APIs

---

## Internal Platform

* API Gateway
* Business Services
* AI Platform
* Event Bus
* Workers
* Scheduler

---

## AI Platform

* ACP Orchestrator
* AI Agents
* Prompt Library
* Memory Layer
* Model Gateway

---

## Integration Layer

Through MCP:

* LinkedIn
* Gmail
* Google Calendar
* Google Drive
* GitHub
* Job Boards
* ATS Platforms
* Object Storage

---

## Infrastructure

* PostgreSQL
* pgvector
* Redis
* Object Storage
* Kubernetes
* Monitoring
* Logging

---

# 8. High-Level System View

```text
                                      User
                                        │
                              Next.js Web Dashboard
                                        │
                              Authentication Layer
                                        │
                                 API Gateway (FastAPI)
                                        │
        ┌─────────────────────────────────────────────────────────┐
        │                  Business Services                      │
        │                                                         │
        │  Resume │ Jobs │ Applications │ Analytics │ Notification│
        └─────────────────────────────────────────────────────────┘
                                        │
                             ACP Orchestrator (LangGraph)
                                        │
     ┌──────────────┬──────────────┬──────────────┬──────────────┐
     │              │              │              │              │
 Resume Agent   Search Agent  Ranking Agent  Apply Agent  Coach Agent
     │              │              │              │              │
     └──────────────┴──────────────┴──────────────┴──────────────┘
                                        │
                                 MCP Client Layer
                                        │
      ┌──────────────┬──────────────┬──────────────┬─────────────┐
      │              │              │              │             │
 LinkedIn       Gmail        Google Drive      ATS APIs    GitHub
      │
      └───────────────────────────────────────────────────────────┘
                                        │
                                External Platforms
```

---

# 9. Major Architectural Layers

The platform is organized into seven logical layers.

### Layer 1 — Presentation

Responsibilities:

* User Interface
* Dashboard
* Authentication
* User interactions

Technology:

* Next.js
* React
* TypeScript

---

### Layer 2 — API Layer

Responsibilities:

* Request validation
* Authentication
* Routing
* Rate limiting

Technology:

* FastAPI

---

### Layer 3 — Business Services

Responsibilities:

* Resume management
* Job management
* Application tracking
* User preferences
* Analytics

---

### Layer 4 — AI Platform

Responsibilities:

* Agent execution
* Workflow orchestration
* Prompt execution
* Memory
* Reasoning

---

### Layer 5 — Integration Layer

Responsibilities:

* MCP Clients
* External tools
* External APIs
* Browser automation

---

### Layer 6 — Data Layer

Responsibilities:

* Persistent storage
* Vector search
* Caching
* Files

---

### Layer 7 — Infrastructure

Responsibilities:

* Containers
* Kubernetes
* Networking
* Monitoring
* Secrets
* Scaling

---

# 10. Quality Attributes

The architecture prioritizes the following non-functional qualities.

| Attribute       | Goal                                                              |
| --------------- | ----------------------------------------------------------------- |
| Scalability     | Horizontal scaling with stateless services                        |
| Reliability     | Graceful degradation and retries                                  |
| Availability    | High uptime through managed infrastructure                        |
| Security        | Encryption, OAuth, least privilege                                |
| Extensibility   | Add new agents, MCP servers, and workflows without major redesign |
| Observability   | Logs, metrics, traces, audit events                               |
| Maintainability | Modular services and well-defined interfaces                      |
| Portability     | Deployable across GCP, AWS, Azure, or self-managed Kubernetes     |

---

# 11. Architectural Constraints

The following constraints guide implementation.

* AI agents must not fabricate factual user information.
* External integrations should be abstracted behind MCP interfaces where practical.
* Agent coordination must use ACP workflows instead of direct dependencies.
* Business services must remain independently deployable.
* Long-running operations must execute asynchronously.
* Sensitive data must never be logged in plaintext.
* Every critical workflow must support retries and failure recovery.

---

# 12. Future Evolution

The architecture is intentionally designed to evolve without major restructuring.

Future capabilities may include:

* Voice-based AI career coaching
* Enterprise multi-tenant deployments
* Organization workspaces
* Additional MCP servers
* New AI agents
* Marketplace for third-party integrations
* AI-powered career analytics
* International compliance modules

These features should be implementable by extending existing architectural layers rather than replacing them.

---

# 13. Document Dependencies

This overview establishes the foundation for the remaining System Architecture sections.

The following documents expand specific aspects of the architecture:

* 01 — Architecture Principles
* 02 — High-Level Architecture
* 03 — Component Architecture
* 04 — Service Architecture
* 05 — AI Agent Layer
* 06 — ACP Architecture
* 07 — MCP Architecture
* 08 — Event-Driven Architecture
* 09 — Data Layer
* 10 — Storage Layer
* 11 — Worker Architecture
* 12 — API Gateway
* 13 — Security Architecture
* 14 — Cloud Deployment
* 15 — Scalability Strategy
* 16 — Failure Recovery
* 17 — Observability
* 18 — Technology Decisions
* 19 — Future Architecture
