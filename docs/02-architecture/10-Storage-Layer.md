# Storage Layer Architecture

**Document ID:** 02.10

**Version:** 1.0

**Status:** Draft

**Last Updated:** 2026-07-12

---

# 1. Purpose

This document defines the Storage Layer of CareerPilot AI.

The Storage Layer is responsible for persisting all application data, documents, AI artifacts, workflow state, logs, embeddings, and analytics in the appropriate storage technology.

The platform intentionally uses multiple storage technologies because different types of data have different access patterns, scalability requirements, and consistency guarantees.

---

# 2. Goals

The Storage Layer should:

- Store every type of data in the most appropriate storage engine.
- Separate transactional, analytical, and AI workloads.
- Support cloud-native storage.
- Enable horizontal scaling.
- Minimize storage costs.
- Support backup and disaster recovery.
- Enable encryption and auditing.
- Be provider independent.

---

# 3. Storage Philosophy

There is no single database.

CareerPilot AI follows a **polyglot persistence** architecture.

Each storage engine is selected according to its strengths.

| Storage Type | Technology |
|--------------|------------|
| Transactional | PostgreSQL |
| Vector | pgvector |
| Cache | Redis |
| Files | Google Cloud Storage |
| Events | Redis Streams / PubSub |
| Logs | OpenTelemetry |
| Metrics | Prometheus |
| Traces | Tempo / Jaeger |

---

# 4. High-Level Storage Architecture

```text
                 Business Services
                        │
        ┌───────────────┼────────────────┐
        ▼               ▼                ▼
 PostgreSQL        Google Cloud     Redis
                    Storage
        │               │                │
        ▼               ▼                ▼
    pgvector      Resume Files      Queue / Cache
                        │
                        ▼
               Analytics Platform
```

---

# 5. Storage Categories

The platform stores several categories of information.

## Structured Data

Examples:

- Users
- Candidate Profiles
- Jobs
- Companies
- Applications
- Skills

Storage:

PostgreSQL

---

## Documents

Examples:

- Resume PDFs
- DOCX
- Cover Letters
- Portfolios
- Certificates

Storage:

Google Cloud Storage

---

## AI Data

Examples:

- Resume Embeddings
- Job Embeddings
- Prompt Metadata
- Retrieval Context

Storage:

pgvector

---

## Temporary Data

Examples:

- Sessions
- OTP
- Cache
- Rate Limits
- Workflow Locks

Storage:

Redis

---

## Operational Data

Examples:

- Logs
- Metrics
- Traces

Storage:

Observability Platform

---

# 6. PostgreSQL Storage

Stores:

- Core business entities
- Relationships
- Configuration
- Metadata
- Workflow records

Characteristics:

- ACID
- Strong consistency
- Transactions
- Referential integrity

---

# 7. Object Storage

Technology:

Google Cloud Storage

Future:

Amazon S3

Stores:

- Resume versions
- Template versions
- Generated DOCX and HTML/PDF outputs
- Attachments
- Generated resumes
- Cover letters
- Browser screenshots
- Interview documents

Objects are immutable whenever possible.

Canonical resume JSON and render metadata are stored in PostgreSQL. Every rendered resume records its content checksum, template version, renderer version, render options, validation outcome, and object-storage reference. A content or template change creates a new artifact rather than overwriting an existing one.

---

# 8. Vector Storage

Technology:

pgvector

Stores embeddings for:

- Resume
- Candidate
- Job
- Skills
- Projects
- Recruiter Messages

Supports:

- Semantic Search
- Recommendation Engine
- RAG
- Similarity Search

---

# 9. Redis Storage

Responsibilities:

- Cache
- Queue broker
- Session store
- Workflow locks
- Distributed mutex
- Temporary state

Redis data is disposable.

Business records must never depend solely on Redis.

---

# 10. Storage Layout

Example object storage layout:

```text
users/
    {user_id}/
        resumes/
        cover-letters/
        portfolios/
        certificates/

companies/

jobs/

applications/

generated/

screenshots/

exports/
```

---

# 11. File Naming

Generated files should use immutable identifiers.

Example:

```
resume_v4_20260712.pdf
```

Avoid mutable names like:

```
resume_final.pdf
resume_latest.pdf
```

---

# 12. Metadata Strategy

Every stored file should have metadata.

Example:

- User ID
- File Type
- MIME Type
- SHA-256 Checksum
- Upload Time
- Version
- Source
- Size

Metadata is stored in PostgreSQL.

---

# 13. Storage Lifecycle

Resume Example

```text
Upload

↓

Virus Scan (Future)

↓

Store File

↓

Extract Metadata

↓

Parse

↓

Generate Embeddings

↓

Index

↓

Ready
```

---

# 14. Data Retention

Examples:

Resume

Keep until user deletes account.

Logs

Retain according to operational policy.

Browser Screenshots

Short-term retention.

Workflow Cache

Automatic expiration.

Retention policies should be configurable.

---

# 15. Archival Strategy

Old versions should be archived instead of deleted when appropriate.

Examples:

- Resume versions
- Cover letters
- Generated documents

Archival enables rollback and auditing.

---

# 16. Encryption

All storage must support:

Encryption at Rest

Encryption in Transit

Server-side encryption should be enabled for object storage.

Sensitive documents should never be publicly accessible.

---

# 17. Backup Strategy

PostgreSQL

- Daily backups
- PITR

Object Storage

- Versioning
- Replication

Redis

- Snapshot

Configuration

- Git

Recovery procedures must be documented and tested.

---

# 18. Disaster Recovery

Recovery objectives should define:

- Recovery Time Objective (RTO)
- Recovery Point Objective (RPO)

Critical business data should support automated recovery.

---

# 19. Performance

Optimize:

- Object size
- Compression
- Connection pooling
- Indexes
- CDN (future)

Avoid storing large binary objects inside PostgreSQL.

---

# 20. Scalability

Storage systems must scale independently.

Examples:

Increase:

- Object Storage capacity
- PostgreSQL replicas
- Redis memory
- Vector indexes

No storage technology should become a bottleneck.

---

# 21. Cost Optimization

Reduce costs by:

- Compressing documents
- Lifecycle policies
- Archiving inactive files
- Removing duplicate uploads
- Cleaning temporary objects

Storage classes should be selected according to access frequency.

---

# 22. Future Storage

Potential additions:

- BigQuery
- ClickHouse
- Data Lake
- Feature Store
- Knowledge Graph
- Iceberg Tables
- Delta Lake

---

# 23. Related Documents

- 02.09 Data Layer
- 08 Database
- 10 Security
- 11 Deployment
