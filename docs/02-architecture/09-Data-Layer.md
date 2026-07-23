# Data Layer Architecture

**Document ID:** 02.09

**Version:** 1.0

**Status:** Draft

**Last Updated:** 2026-07-12

---

# 1. Purpose

This document defines the Data Layer architecture of CareerPilot AI.

The Data Layer is responsible for storing, organizing, indexing, retrieving, securing, and governing all application data.

It provides a unified data platform for the business services, AI agents, analytics, and external integrations.

This document focuses on architecture rather than the detailed database schema, which is defined in the Database documentation.

---

# 2. Goals

The Data Layer should:

- Support transactional workloads.
- Support AI workloads.
- Support semantic search.
- Support analytics.
- Support event-driven processing.
- Enable horizontal scaling.
- Minimize data duplication.
- Preserve data integrity.
- Support GDPR-compliant deletion.
- Support future multi-tenancy.

---

# 3. Design Principles

The Data Layer follows these principles.

## Single Source of Truth

Every business entity has exactly one owner.

Examples:

Candidate

↓

Candidate Service

↓

PostgreSQL

No duplicate ownership.

---

## Separation of Storage Types

Different data belongs in different storage systems.

Relational Data

↓

PostgreSQL

Vector Data

↓

pgvector

Files

↓

Object Storage

Cache

↓

Redis

Logs

↓

Observability Platform

Events

↓

Event Bus

---

## Domain Ownership

Each domain owns its own data.

Candidate owns candidate data.

Jobs own job data.

Applications own application data.

No cross-domain ownership.

---

## Immutable History

Important business events should never be overwritten.

Instead:

- Version records
- Store history
- Audit changes

---

# 4. High-Level Data Architecture

```text
                    Applications
                         │
                         ▼
                 Business Services
                         │
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
 PostgreSQL        Object Storage      Redis
        │                │                │
        ▼                ▼                ▼
 pgvector        Resume Files      Cache / Queue
                         │
                         ▼
                Analytics Platform
```

---

# 5. Data Storage Technologies

| Storage | Purpose |
|----------|---------|
| PostgreSQL | Primary transactional database |
| pgvector | Semantic embeddings |
| Redis | Cache, sessions, queues |
| Google Cloud Storage | Resume and document storage |
| Event Bus | Workflow events |
| Analytics Warehouse (Future) | BI and reporting |

---

# 6. Primary Database

Technology:

PostgreSQL

Stores:

- Users
- Candidate Profiles
- Jobs
- Companies
- Applications
- Skills
- Preferences
- Workflows
- Agent Metadata

PostgreSQL is the primary source of truth.

---

# 7. Vector Database

Technology:

pgvector

Stores embeddings for:

- Resume
- Job Description
- Skills
- Projects
- Cover Letters
- Recruiter Messages

Supports:

- Semantic Search
- Similarity Matching
- Recommendation Engine
- AI Context Retrieval

---

# 8. Object Storage

Technology:

Google Cloud Storage

Future:

Amazon S3

Stores:

- Resume PDFs
- DOCX files
- Cover Letters
- Attachments
- Portfolio Files
- Screenshots
- Generated Documents

Files are never stored inside PostgreSQL.

---

# 9. Redis

Redis is used for:

- Session storage
- Cache
- Queue broker
- Rate limiting
- Distributed locks
- Temporary workflow state

Redis is never the system of record.

---

# 10. Event Storage

Workflow events are published to the Event Bus.

Events are operational messages.

Business data is stored in PostgreSQL.

Future versions may introduce event replay.

---

# 11. Data Domains

The platform consists of the following logical domains.

Candidate

Resume

Jobs

Companies

Applications

Interview

Career Intelligence

Notifications

AI Metadata

Workflow State

Analytics

Each domain owns its data.

---

# 12. Data Ownership

| Domain | Owner |
|---------|------|
| Candidate | Candidate Service |
| Resume | Resume Service |
| Jobs | Job Service |
| Applications | Application Service |
| AI Metadata | AI Platform |
| Notifications | Notification Service |
| Analytics | Analytics Service |

No service writes directly into another domain.

---

# 13. Data Lifecycle

Example:

Resume

↓

Upload

↓

Parse

↓

Extract Metadata

↓

Generate Embeddings

↓

Store File

↓

Store Metadata

↓

Store Embedding

↓

Index

↓

Ready for Search

---

# 14. Data Access Pattern

Applications

↓

REST API

↓

Business Service

↓

Repository Layer

↓

Database

AI Agents never communicate directly with databases.

AI agents obtain data through business services or approved MCP tools.

---

# 15. Repository Pattern

Every aggregate root has its own repository.

Examples:

CandidateRepository

ResumeRepository

JobRepository

ApplicationRepository

CompanyRepository

Repositories isolate business logic from storage implementation.

---

# 16. Versioning

Version the following:

Resume

Candidate Profile

Cover Letter

Canonical Resume JSON

Resume Render Metadata

Prompt

Job Description Snapshot

Application Snapshot

Versioning enables reproducibility and auditing.

---

# 17. Data Consistency

Transactional operations use PostgreSQL transactions.

Cross-service consistency is achieved through:

- Domain Events
- ACP Workflows
- Retry Policies
- Idempotent Consumers

Distributed transactions are avoided.

---

# 18. Data Retention

Retention policies should define:

Resume Files

Workflow Logs

Agent Executions

Events

Notifications

Analytics

Deleted users should have their personal data removed or anonymized according to applicable regulations and business requirements.

---

# 19. Security

Sensitive data includes:

- Resume
- Email
- Phone Number
- OAuth Tokens
- Recruiter Messages

Requirements:

- Encryption at rest
- Encryption in transit
- Access control
- Audit logs
- Secret management

Least privilege must be enforced.

---

# 20. Backup & Recovery

Primary Database

- Automated backups
- Point-in-time recovery

Object Storage

- Versioning
- Replication

Redis

- Snapshotting (where appropriate)

Recovery procedures should be tested regularly.

---

# 21. Performance

Target objectives:

- Indexed queries
- Efficient pagination
- Optimized joins
- Vector indexes
- Connection pooling

Large binary objects must not reside in PostgreSQL.

---

# 22. Scalability

The Data Layer supports:

- Read replicas
- Connection pooling
- Horizontal workers
- Independent object storage scaling
- Independent vector search scaling

Storage technologies may evolve independently.

---

# 23. Future Enhancements

Future capabilities may include:

- Data Warehouse
- Feature Store
- Knowledge Graph
- Multi-region replication
- Data Lake
- Real-time analytics
- Cross-region disaster recovery

---

# 24. Related Documents

- 02.08 Event-Driven Architecture
- 02.10 Storage Layer
- 08 Database
- 10 Security
- 11 Deployment
- 13 Observability
