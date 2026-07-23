# CareerPilot AI

# Document 02.02 — High-Level Architecture

**Version:** 1.0
**Status:** Draft
**Last Updated:** 2026-07-12

---

# 1. Purpose

This document defines the high-level architecture of CareerPilot AI.

It explains how all major platform components interact while remaining independent, scalable, cloud-native, and AI-first.

The goal is to establish a clear architectural blueprint before implementation begins.

---

# 2. Architectural Overview

CareerPilot AI follows a layered, event-driven, AI-native architecture.

The platform consists of:

* Client Applications
* API Platform
* Business Services
* AI Platform
* ACP Orchestration
* MCP Integration Layer
* Data Platform
* Infrastructure Platform

Each layer has a clearly defined responsibility.

---

# 3. High-Level Architecture

```text
                                    USER
                                      │
                    ┌────────────────────────────────┐
                    │        Client Applications      │
                    │────────────────────────────────│
                    │ • Next.js Web Dashboard        │
                    │ • Browser Extension            │
                    │ • Future Mobile App            │
                    │ • Public REST API              │
                    └────────────────────────────────┘
                                      │
                                      ▼
                    ┌────────────────────────────────┐
                    │         API Gateway            │
                    │────────────────────────────────│
                    │ Authentication                 │
                    │ Authorization                  │
                    │ Rate Limiting                  │
                    │ Request Validation             │
                    │ API Versioning                 │
                    └────────────────────────────────┘
                                      │
             ┌────────────────────────┼────────────────────────┐
             ▼                        ▼                        ▼
   Resume Service            Job Service            Application Service
             │                        │                        │
             ▼                        ▼                        ▼
                  Notification Service      Analytics Service
                                      │
                                      ▼
                    ┌────────────────────────────────┐
                    │       ACP Orchestrator         │
                    │  (LangGraph Supervisor Agent)  │
                    └────────────────────────────────┘
                                      │
──────────────────────────────────────────────────────────────────────────────

 Resume Agent

 Job Discovery Agent

 Ranking Agent

 Resume Optimizer Agent

 Cover Letter Agent

 Application Agent

 Recruiter Agent

 Interview Agent

 Career Coach Agent

 Notification Agent

──────────────────────────────────────────────────────────────────────────────
                                      │
                                      ▼
                    ┌────────────────────────────────┐
                    │         MCP Client Layer       │
                    └────────────────────────────────┘
                                      │
──────────────────────────────────────────────────────────────────────────────

 LinkedIn MCP

 Gmail MCP

 Calendar MCP

 GitHub MCP

 Google Drive MCP

 ATS MCP

 Browser MCP

 PostgreSQL MCP

 Filesystem MCP

──────────────────────────────────────────────────────────────────────────────
                                      │
                                      ▼
                         External Systems & APIs
```

---

# 4. Architectural Layers

The platform is organized into eight logical layers.

## Layer 1 — Presentation Layer

Responsibilities:

* User Interface
* Authentication
* Dashboard
* User interactions
* Browser extension

Technology:

* Next.js
* React
* TypeScript
* Tailwind CSS

No business logic should exist in this layer.

---

## Layer 2 — API Layer

Responsibilities:

* Authentication
* Authorization
* Request validation
* API routing
* API versioning
* Rate limiting

Technology:

* FastAPI

The API layer acts as the entry point to the platform.

---

## Layer 3 — Business Domain Layer

Responsible for business capabilities.

Services include:

* User Service
* Resume Service
* Job Service
* Application Service
* Notification Service
* Analytics Service
* Billing Service (future)

Business services do not communicate directly with external platforms.

---

## Layer 4 — AI Platform

The AI platform provides intelligent reasoning.

Responsibilities:

* Resume analysis
* Semantic search
* Resume optimization
* Cover letter generation
* Career recommendations
* Interview preparation

AI is implemented through specialized agents coordinated by ACP.

---

## Layer 5 — ACP Layer

ACP is responsible for internal agent communication.

Responsibilities:

* Task routing
* Workflow execution
* Message passing
* Retry policies
* Human approval checkpoints
* Workflow state

Technology:

* LangGraph

ACP coordinates agents but does not access external systems directly.

---

## Layer 6 — MCP Layer

MCP provides standardized access to tools and external resources.

Responsibilities:

* Tool discovery
* Tool execution
* Authentication
* Context sharing

Supported integrations:

* Gmail
* Google Drive
* GitHub
* LinkedIn
* Calendar
* ATS
* Browser automation
* Database
* Filesystem

---

## Layer 7 — Data Platform

Persistent storage.

Includes:

* PostgreSQL
* pgvector
* Redis
* Object Storage

Stores:

* Users
* Jobs
* Applications
* Resume versions
* Embeddings
* Agent state
* Analytics

---

## Layer 8 — Infrastructure

Supports:

* Docker
* Kubernetes
* Cloud Run
* Terraform
* Monitoring
* Logging
* Secrets
* CI/CD

---

# 5. Request Flow

A typical user request flows through the platform.

```text
User

↓

Next.js

↓

FastAPI

↓

Business Service

↓

ACP Workflow

↓

AI Agent(s)

↓

MCP Tool(s)

↓

External Platform

↓

ACP Response

↓

Business Service

↓

API

↓

Dashboard
```

---

# 6. Example Workflow

Resume Upload

```text
User

↓

Upload Resume

↓

Resume Service

↓

Resume Uploaded Event

↓

Resume Agent

↓

Canonical Candidate Profile

↓

Embedding Generation

↓

Database

↓

Dashboard Updated
```

---

Job Search

```text
User

↓

Search Jobs

↓

Job Service

↓

ACP

↓

Job Discovery Agent

↓

LinkedIn MCP

↓

Job Results

↓

Ranking Agent

↓

Dashboard
```

---

Application

```text
User

↓

Apply

↓

Resume Optimizer

↓

Cover Letter Agent

↓

Human Approval

↓

Application Agent

↓

Browser MCP / ATS MCP

↓

Application Stored

↓

Notification
```

---

# 7. Platform Responsibilities

## Business Services

Responsible for:

* CRUD operations
* Business validation
* Persistence
* Domain logic

Never responsible for:

* LLM reasoning
* Browser automation
* Prompt management

---

## ACP

Responsible for:

* AI workflow orchestration
* Agent communication
* Retry logic
* State transitions
* Workflow execution

---

## MCP

Responsible for:

* External integrations
* Tool execution
* Authentication
* Standardized interfaces

---

## AI Agents

Responsible for:

* Reasoning
* Recommendations
* Text generation
* Ranking
* Resume analysis

---

# 8. Event-Driven Communication

Long-running operations communicate through events.

Examples:

```text
ResumeUploaded

ResumeParsed

JobsDiscovered

JobsRanked

ResumeOptimized

CoverLetterGenerated

ApplicationSubmitted

ApplicationFailed

InterviewScheduled

InterviewCompleted
```

Events enable loose coupling between services.

---

# 9. Technology Stack

| Layer               | Technology                             |
| ------------------- | -------------------------------------- |
| Frontend            | Next.js + React + TypeScript           |
| Backend             | FastAPI                                |
| AI Orchestration    | LangGraph                              |
| Agent Communication | ACP                                    |
| Tool Integration    | MCP                                    |
| Browser Automation  | Playwright                             |
| Queue               | Redis + Celery (or Temporal in future) |
| Database            | PostgreSQL                             |
| Vector Search       | pgvector                               |
| Cache               | Redis                                  |
| Storage             | Google Cloud Storage / Amazon S3       |
| Monitoring          | OpenTelemetry + LangSmith              |
| Deployment          | Docker + Kubernetes                    |

---

# 10. Scalability Strategy

The architecture supports independent scaling.

Examples:

* Scale API independently.
* Scale workers independently.
* Scale AI agents independently.
* Scale browser automation independently.
* Scale databases separately.

No layer assumes a single server deployment.

---

# 11. Security Boundaries

Every layer has clear security responsibilities.

Presentation:

* Authentication
* Session handling

API:

* Authorization
* Validation

Business:

* Domain authorization

AI:

* Prompt safety
* Human approval

MCP:

* Tool permissions
* OAuth

Infrastructure:

* Secrets
* Encryption
* Network isolation

---

# 12. Future Expansion

This architecture supports future capabilities without major redesign.

Future modules include:

* Voice AI
* Multi-tenant organizations
* Enterprise administration
* Marketplace integrations
* Additional MCP servers
* Additional AI agents
* Resume marketplace
* Learning platform
* Career analytics

---

# 13. Success Criteria

The architecture is successful when:

* New AI agents can be added without changing existing agents.
* New MCP servers can be integrated without modifying business services.
* ACP workflows remain reusable.
* Services scale independently.
* AI components remain replaceable.
* The platform supports cloud-native deployment.
* Public SaaS deployment requires no architectural redesign.

---

# 14. Related Documents

This document is expanded by:

* Component Architecture
* Service Architecture
* AI Agent Architecture
* ACP Architecture
* MCP Architecture
* Event-Driven Architecture
* Database Design
* Deployment Architecture
* Security Architecture
* Scalability Strategy
