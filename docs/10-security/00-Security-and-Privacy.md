# Security and Privacy Design

**Document ID:** 10.00  
**Status:** Draft

## Purpose

Defines implementation controls for CareerPilot's sensitive candidate, resume, integration, and automation data. This supplements the architecture-level [Security Architecture](../02-architecture/13-Security-Architecture.md).

## Required Controls

- Authenticate users and services; enforce object-level authorization and least privilege.
- Encrypt data in transit and at rest; store secrets only in managed secret storage.
- Use OAuth with minimum scopes for integrations; support revocation and token refresh.
- Keep resumes, renders, screenshots, and attachments private in object storage; use short-lived signed URLs.
- Redact PII, credentials, cookies, and document contents from logs/traces.
- Maintain immutable audit events for approvals, submissions, integration access, and admin actions.
- Support export, deletion, consent withdrawal, retention, and data classification.

## AI and Automation Controls

AI-generated factual changes require approval. Submission, outreach, and calendar updates require a user policy and an auditable authorization event. Prompt injection, untrusted job descriptions, and tool output are treated as untrusted input.

## Incident Readiness

Maintain severity definitions, credential-revocation procedures, backup restoration exercises, and a disclosure/escalation process. Security findings produce tracked remediation work.

## Related Documents

- [13-Security-Architecture.md](../02-architecture/13-Security-Architecture.md)
- [16-Failure-Recovery.md](../02-architecture/16-Failure-Recovery.md)
