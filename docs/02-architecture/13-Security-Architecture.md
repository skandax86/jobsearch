# Security Architecture

**Document ID:** 02.13

**Version:** 1.0

**Status:** Draft

**Last Updated:** 2026-07-12

---

# 1. Purpose

This document defines the security architecture of CareerPilot AI.

CareerPilot AI processes highly sensitive personal information including resumes, employment history, recruiter communications, interview schedules, authentication credentials, and user preferences.

Security must be designed into every layer of the platform rather than added later.

---

# 2. Security Objectives

The platform shall ensure:

- Confidentiality
- Integrity
- Availability
- Authentication
- Authorization
- Accountability
- Auditability
- Privacy
- Compliance

---

# 3. Security Principles

The platform follows these principles.

## Zero Trust

Every request must be authenticated.

Every operation must be authorized.

No implicit trust exists between services.

---

## Least Privilege

Every service, user, agent and MCP server receives only the permissions required.

---

## Defense in Depth

Security exists at multiple layers:

- Client
- API
- Services
- ACP
- MCP
- Database
- Storage
- Infrastructure

---

## Secure by Default

Security should never depend on optional configuration.

---

## Fail Secure

Failures must deny access instead of granting access.

---

# 4. Security Architecture

```text
                Internet
                    │
                    ▼
           Load Balancer / WAF
                    │
                    ▼
              API Gateway
                    │
        Authentication Layer
                    │
        Authorization Layer
                    │
        Business Services
                    │
     ACP / AI Agent Layer
                    │
           MCP Integrations
                    │
       Database / Storage Layer
```

---

# 5. Authentication

Supported methods:

- Email & Password
- Google OAuth
- GitHub OAuth
- Microsoft OAuth (Future)

Authentication uses:

- JWT Access Token
- Refresh Token

Passwords must be hashed using Argon2 or bcrypt.

Passwords are never stored in plaintext.

---

# 6. Authorization

Role-Based Access Control (RBAC)

Initial Roles:

- Candidate
- Administrator
- Support

Future Roles:

- Recruiter
- Organization Admin
- Enterprise Administrator

Every request is authorized.

---

# 7. Identity Management

Each user has:

- User ID
- Roles
- Permissions
- Session Information
- MFA Status (Future)

Identity is the foundation for all authorization decisions.

---

# 8. Session Security

Requirements:

- Secure Cookies
- HttpOnly
- SameSite
- Session Expiration
- Token Rotation

Sessions should be revocable.

---

# 9. API Security

Every API request requires:

Authentication

↓

Authorization

↓

Validation

↓

Rate Limiting

↓

Business Logic

↓

Audit Logging

HTTPS is mandatory.

---

# 10. AI Security

AI agents must:

- Never fabricate resume information.
- Never leak another user's data.
- Respect permission boundaries.
- Produce structured outputs.
- Require approval for sensitive actions.

Prompt injection attempts should be detected and mitigated where practical.

---

# 11. ACP Security

ACP validates:

- Workflow ownership
- Agent permissions
- Workflow integrity
- Message authenticity

Agents cannot execute arbitrary workflows.

---

# 12. MCP Security

Every MCP server:

- Uses secure authentication
- Stores no plaintext secrets
- Validates permissions
- Supports audit logging

Browser automation runs in isolated environments.

---

# 13. Database Security

Requirements:

- Encryption at rest
- TLS connections
- Least-privilege accounts
- Parameterized queries
- Connection pooling

Direct database access is restricted.

---

# 14. Storage Security

Object Storage:

- Private buckets
- Signed URLs
- Versioning
- Encryption

Resume files are never publicly accessible.

---

# 15. Secret Management

Secrets include:

- OAuth Credentials
- API Keys
- Database Passwords
- JWT Signing Keys
- Encryption Keys

Secrets are stored in a managed secret manager.

Examples:

- Google Secret Manager
- AWS Secrets Manager
- HashiCorp Vault

Secrets are never committed to Git.

---

# 16. Encryption

Encryption in Transit

- TLS 1.2+

Encryption at Rest

- Database
- Object Storage
- Backups

Sensitive application data should use strong encryption algorithms and managed key services where available.

---

# 17. Input Validation

Validate:

- Request Body
- Query Parameters
- Uploaded Files
- JSON Schema
- File Type
- File Size

Never trust client input.

---

# 18. File Upload Security

Resume uploads require:

- MIME Validation
- Extension Validation
- Size Validation
- Malware Scanning (Future)
- Secure Storage

Executable files are rejected.

---

# 19. Logging & Auditing

Audit events include:

- Login
- Logout
- Resume Upload
- Resume Modification
- Job Application
- Permission Changes
- MCP Access
- Admin Actions

Audit logs are immutable.

---

# 20. Privacy

Personal data includes:

- Name
- Email
- Phone
- Resume
- Employment History
- Recruiter Messages

Users should be able to:

- Download their data
- Delete their account
- Manage consent
- Control connected integrations

---

# 21. Compliance

The architecture should support:

- GDPR
- CCPA (Future)
- SOC 2 (Future)

Compliance requirements should influence data retention, consent, and auditing.

---

# 22. Rate Limiting

Apply limits for:

- Login
- Resume Upload
- AI Requests
- Browser Automation
- Public APIs

Limits should be configurable.

---

# 23. Browser Security

Playwright workers:

- Execute in isolated containers
- Use temporary profiles
- Destroy sessions after completion
- Clear cookies
- Remove temporary files

Persistent browser state should be avoided unless required.

---

# 24. Dependency Security

All dependencies should:

- Be scanned regularly
- Be updated
- Have known vulnerabilities monitored

CI/CD should include dependency scanning.

---

# 25. Infrastructure Security

Infrastructure should implement:

- Private networking
- IAM
- Firewalls
- WAF
- Kubernetes RBAC
- Network Policies

Production infrastructure should be isolated from development environments.

---

# 26. Monitoring & Detection

Monitor:

- Failed Logins
- Token Abuse
- API Abuse
- Suspicious MCP Activity
- Prompt Injection Attempts
- Rate Limit Violations

Security events should generate alerts.

---

# 27. Incident Response

The platform should support:

- Incident Detection
- Alerting
- Containment
- Investigation
- Recovery
- Post-Incident Review

Security incidents should be traceable.

---

# 28. Future Enhancements

Future capabilities:

- MFA
- Passkeys
- Device Trust
- Risk-Based Authentication
- Secret Rotation
- DLP
- Data Classification
- Security Score Dashboard

---

# 29. Related Documents

- 02.12 API Gateway
- 02.07 MCP Architecture
- 02.06 ACP Architecture
- 09 Prompts
- 11 Deployment
- 13 Observability