# Component Architecture

**Document ID:** 02.03

**Version:** 1.0

**Status:** Draft

**Last Updated:** 2026-07-12

---

# 1. Purpose

This document defines the major software components of CareerPilot AI, their responsibilities, ownership boundaries, dependencies, and interactions.

The objective is to establish clear component boundaries before implementation begins.

This document does **not** describe deployment units or microservices. Those are defined in the Service Architecture document.

---

# 2. Goals

The component architecture should:

- Promote separation of concerns.
- Minimize coupling between components.
- Maximize cohesion within components.
- Enable independent evolution.
- Support AI-driven workflows.
- Support cloud-native deployment.
- Be understandable by both engineers and AI coding agents.

---

# 3. Component Design Principles

Each component must:

- Own a single business capability.
- Expose well-defined interfaces.
- Avoid direct access to another component's internal state.
- Be independently testable.
- Support observability.
- Fail gracefully.
- Remain replaceable.

---

# 4. High-Level Component Diagram

```text
                         Client Applications
                                 │
                                 ▼
                          API Gateway Layer
                                 │
      ┌──────────────┬──────────────┬──────────────┐
      ▼              ▼              ▼
 Candidate      Job Discovery   Application
 Component        Component       Component
      │              │              │
      └──────────────┴──────────────┘
                     │
                     ▼
              AI Platform Component
                     │
             ACP Orchestrator
                     │
         Specialized AI Agents
                     │
               MCP Integration
                     │
            External Platforms
                     │
              Shared Data Platform
```

---

# 5. Core Components

The platform consists of the following primary components.

## 5.1 Candidate Component

### Responsibilities

- User profile management
- Career preferences
- Skills
- Experience
- Education
- Certifications
- Candidate settings

### Owns

- Candidate Profile
- Preferences
- Career Goals

### Does Not Own

- Jobs
- Applications
- AI workflows

---

## 5.2 Resume Component

### Responsibilities

- Resume upload
- Resume versioning
- Resume parsing
- Canonical resume-content generation and validation
- Truthful, job-tailored content proposals
- Template selection and deterministic rendering
- Resume storage and render-artifact provenance

### Owns

- Resume files
- Resume metadata
- Resume versions
- Canonical Resume JSON
- Resume templates and render metadata

### Rendering Rule

The Resume Component separates content from presentation. AI agents produce validated structured Resume JSON, not raw document markup. Approved templates render that JSON to LaTeX/PDF, DOCX, or HTML; PDF is never the editable source of truth.

---

## 5.3 Job Discovery Component

Responsibilities:

- Job ingestion
- Job normalization
- Duplicate detection
- Company enrichment
- Salary normalization

Sources:

- LinkedIn
- Greenhouse
- Lever
- Workday
- Company career pages

---

## 5.4 Matching Component

Responsible for:

- Semantic matching
- Resume scoring
- Skill matching
- Recommendation ranking

Inputs:

- Candidate Profile
- Job Description

Outputs:

- Match Score
- Ranking Explanation

---

## 5.5 Application Component

Responsible for:

- Application lifecycle
- Status tracking
- Resume selection
- Cover letter selection
- Submission history

Application states include:

- Draft
- Ready
- Submitted
- Assessment
- Interview
- Offer
- Rejected
- Withdrawn

---

## 5.6 AI Platform Component

Responsible for:

- Agent execution
- Prompt execution
- Workflow orchestration
- LLM interaction
- Memory management

The AI Platform does not own business data.

---

## 5.7 Notification Component

Responsible for:

- Email
- Push notifications
- In-app notifications
- Slack (future)
- Teams (future)

---

## 5.8 Analytics Component

Responsible for:

- User metrics
- Job metrics
- Conversion funnels
- AI usage
- Platform KPIs

---

## 5.9 Authentication Component

Responsible for:

- Login
- OAuth
- JWT
- Session management
- Permissions

---

## 5.10 Integration Component

Responsible for:

- MCP clients
- External APIs
- Browser automation
- OAuth token management

---

# 6. Component Dependencies

Allowed dependencies:

Client

↓

API Gateway

↓

Business Components

↓

AI Platform

↓

MCP

↓

External Systems

No component may bypass these dependency rules without an approved ADR.

---

# 7. Communication Model

Components communicate using:

- REST APIs
- Domain events
- ACP messages
- Queue messages

Direct database access between components is prohibited.

---

# 8. Shared Components

The following utilities are shared across the platform:

- Logging
- Configuration
- Authentication
- Secrets
- Monitoring
- Feature Flags
- Metrics
- Error Handling

Shared components must remain stateless.

---

# 9. Error Handling

Each component must:

- Validate inputs.
- Return typed errors.
- Log failures.
- Emit metrics.
- Retry transient failures.
- Never expose internal exceptions to clients.

---

# 10. Scalability

Each component must support independent scaling.

Examples:

- Scale Job Discovery workers separately.
- Scale AI agents separately.
- Scale Browser Automation separately.
- Scale Notification workers separately.

No component should assume co-location with another component.

---

# 11. Security

Every component must:

- Authenticate requests.
- Authorize operations.
- Validate input.
- Protect sensitive data.
- Emit audit logs.

---

# 12. Observability

Each component must expose:

- Structured logs
- Metrics
- Traces
- Health checks
- Readiness probes

---

# 13. Future Components

Future releases may introduce:

- Billing Component
- Organization Component
- Referral Component
- Marketplace Component
- Learning Component
- Salary Intelligence Component

The architecture should support these additions without modifying existing component boundaries.

---

# 14. Related Documents

- 02.02 High-Level Architecture
- 02.04 Service Architecture
- 03 Domain Model
- 04 AI Agent Architecture
- 08 Database Design
