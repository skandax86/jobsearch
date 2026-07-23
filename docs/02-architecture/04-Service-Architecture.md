# Service Architecture

**Document ID:** 02.04

**Version:** 1.0

**Status:** Draft

**Last Updated:** 2026-07-12

---

# 1. Purpose

This document defines the deployable services that make up the CareerPilot AI platform.

Unlike the Component Architecture, which focuses on logical responsibilities, the Service Architecture describes the runtime services, ownership boundaries, communication patterns, and deployment strategy.

---

# 2. Goals

The service architecture should:

- Support independent deployment.
- Enable horizontal scaling.
- Minimize service coupling.
- Support asynchronous workflows.
- Be cloud-native.
- Be resilient to partial failures.
- Allow future migration to microservices if required.

---

# 3. Service Architecture Philosophy

The platform follows a **Modular Monolith First** approach.

Initial releases will be deployed as a small number of well-defined services with clear domain boundaries.

As scale increases, services can be extracted into independent microservices without changing business logic.

This avoids premature microservice complexity while preserving future scalability.

---

# 4. Runtime Services

The platform consists of the following runtime services.

| Service | Responsibility |
|----------|----------------|
| Web Application | User interface |
| API Service | Public REST API |
| AI Orchestrator | ACP workflow execution |
| Worker Service | Background jobs |
| Browser Automation Service | Job application automation |
| MCP Gateway | External integrations |
| Database | Persistent storage |
| Redis | Cache, queues, sessions |
| Object Storage | Resume & document storage |
| Monitoring Stack | Logs, metrics, tracing |

---

# 5. Service Diagram

```text
                   User
                     │
              Next.js Web App
                     │
                     ▼
              API Service (FastAPI)
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
 Candidate      Jobs        Applications
                     │
                     ▼
             AI Orchestrator
              (LangGraph)
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
     AI Agents    Worker      MCP Gateway
                     │
                     ▼
             Browser Automation
                     │
             External Platforms
```

---

# 6. Web Application

## Technology

- Next.js
- React
- TypeScript
- Tailwind CSS

### Responsibilities

- Authentication
- Dashboard
- Resume upload
- Job search UI
- Application tracking
- Interview preparation
- User settings

The frontend contains no business logic.

---

# 7. API Service

## Technology

FastAPI

### Responsibilities

- REST APIs
- Authentication
- Authorization
- Validation
- Domain orchestration
- Event publishing

The API Service is stateless.

---

# 8. AI Orchestrator

## Technology

LangGraph

### Responsibilities

- Execute ACP workflows
- Coordinate agents
- Maintain workflow state
- Retry failed tasks
- Handle approvals
- Publish workflow events

This service never communicates directly with users.

---

# 9. Worker Service

Handles long-running asynchronous tasks.

Examples:

- Resume parsing
- Embedding generation
- Job crawling
- Company enrichment
- ATS scoring
- Notification delivery
- Analytics aggregation

Workers consume messages from queues.

---

# 10. Browser Automation Service

Technology:

- Playwright

Responsibilities:

- Easy Apply automation
- Form completion
- File uploads
- Screenshot capture
- Session management

Browser automation is isolated from the API service.

---

# 11. MCP Gateway

Responsibilities:

- Tool discovery
- Tool execution
- OAuth management
- Connection pooling
- External API abstraction

Supported integrations include:

- LinkedIn
- Greenhouse
- Lever
- Workday
- Gmail
- Calendar
- GitHub
- Google Drive

---

# 12. Database Service

Technology:

- PostgreSQL

Responsibilities:

- User data
- Resume metadata
- Job metadata
- Applications
- Workflow state
- Analytics

The database is accessed only through the API service.

---

# 13. Vector Search

Technology:

- pgvector

Stores:

- Resume embeddings
- Job embeddings
- Skill embeddings

Supports semantic search and ranking.

---

# 14. Redis

Responsibilities:

- Cache
- Queue broker
- Session storage
- Rate limiting
- Distributed locks

---

# 15. Object Storage

Technology:

- Google Cloud Storage
- Amazon S3 (future)

Stores:

- PDF resumes
- Cover letters
- Attachments
- Generated documents

---

# 16. Monitoring Stack

Technology:

- OpenTelemetry
- Prometheus
- Grafana
- LangSmith

Responsibilities:

- Metrics
- Logs
- Traces
- AI execution monitoring
- Prompt usage
- Cost tracking

---

# 17. Communication Patterns

| Pattern | Usage |
|----------|-------|
| REST | Client → API |
| ACP | Agent ↔ Agent |
| MCP | Agent → External Tools |
| Events | Internal async communication |
| Queue | Background jobs |

---

# 18. Service Ownership

| Service | Owns |
|----------|------|
| Web | Presentation |
| API | Business logic |
| AI Orchestrator | Workflow execution |
| Worker | Background processing |
| Browser Service | Automation |
| MCP Gateway | External integrations |
| PostgreSQL | Structured data |
| Redis | Temporary state |
| Object Storage | Files |

No two services should own the same business data.

---

# 19. Deployment Strategy

Initial deployment:

- 1 Web Service
- 1 API Service
- 1 AI Orchestrator
- N Worker replicas
- N Browser Automation replicas
- 1 PostgreSQL instance
- 1 Redis instance

Each service scales independently.

---

# 20. Scaling Strategy

Horizontal scaling is preferred.

Examples:

- Increase Worker replicas during heavy resume processing.
- Increase Browser Automation replicas during bulk applications.
- Scale API independently from AI services.
- Scale AI Orchestrator separately for complex workflows.

---

# 21. Failure Handling

Every service must implement:

- Health checks
- Readiness probes
- Retry policies
- Timeouts
- Circuit breakers
- Graceful shutdown

Failures should be isolated to the affected service.

---

# 22. Security

All service-to-service communication must use authenticated channels.

Secrets are stored in a managed secret store.

No service may hardcode credentials.

Least-privilege access must be enforced.

---

# 23. Future Service Extraction

The following domains may become standalone services as the platform grows:

- Billing
- Notifications
- Analytics
- AI Gateway
- Candidate Profile
- Job Discovery
- Career Intelligence

The modular architecture should allow extraction without major code changes.

---

# 24. Related Documents

- 02.03 Component Architecture
- 02.05 AI Agent Layer
- 02.06 ACP Architecture
- 02.07 MCP Architecture
- 08 Database Design
- 11 Deployment Architecture