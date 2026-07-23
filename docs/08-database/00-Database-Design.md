# Database Design

**Document ID:** 08.00  
**Status:** Draft

## Purpose

Defines the logical PostgreSQL data model and persistence rules. Migration files, SQLAlchemy models, and generated ERDs must conform to the domain boundaries in `03-domain`.

## Core Tables by Domain

| Domain | Initial tables |
|---|---|
| Identity | users, sessions, consents, integration_connections |
| Candidate | candidate_profiles, candidate_facts, preferences, automation_policies |
| Resume | resumes, resume_versions, resume_contents, resume_templates, resume_renders |
| Jobs | companies, job_postings, job_sources, job_snapshots |
| Intelligence | job_matches, skill_gaps, recommendations, feedback_events |
| Applications | applications, application_packages, application_attempts, status_history, interviews |
| Platform | workflows, workflow_tasks, agent_executions, approvals, outbox_events, audit_events |

## Rules

- Use UUID primary keys, UTC timestamps, and ownership/tenant columns on user-scoped records.
- Enforce foreign keys and state-transition invariants where relationally possible.
- Store source documents and rendered files in object storage; keep object keys, checksums, MIME type, and provenance in PostgreSQL.
- Store canonical resume JSON in a versioned JSONB column validated by the application schema; do not store raw renderer markup as canonical content.
- Use pgvector for derived embeddings; embedding model/version is mandatory metadata.
- Publish events through a transactional outbox, not best-effort dual writes.

## Indexing and Retention

Index owner + state + timestamp access paths, normalized job source identity, workflow status, and vector similarity queries. Time-partition append-heavy audit, execution, and analytics tables as volume requires. Apply deletion/retention policies by data classification.

## Related Documents

- [00-Domain-Overview.md](../03-domain/00-Domain-Overview.md)
- [09-Data-Layer.md](../02-architecture/09-Data-Layer.md)
