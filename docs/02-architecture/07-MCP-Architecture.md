# MCP Architecture

**Document ID:** 02.07

**Version:** 1.0

**Status:** Draft

**Last Updated:** 2026-07-12

---

# 1. Purpose

This document defines how CareerPilot AI integrates with external tools, applications, services, files, and APIs using the Model Context Protocol (MCP).

MCP provides a standardized interface that allows AI agents to discover, authenticate, and interact with external resources without requiring platform-specific implementation logic.

ACP coordinates AI agents.

MCP enables those agents to interact with the outside world.

---

# 2. Goals

The MCP layer should:

- Standardize external integrations.
- Decouple agents from third-party APIs.
- Support plug-and-play tool integrations.
- Centralize authentication.
- Improve security.
- Enable observability.
- Support future MCP servers with minimal changes.

---

# 3. Design Principles

Every integration must:

- Follow the MCP specification.
- Be independently deployable.
- Support authentication.
- Return structured responses.
- Handle retries gracefully.
- Expose metadata.
- Emit logs and metrics.

Agents never call external systems directly.

---

# 4. MCP Architecture

```text
                     AI Agent
                         │
                         ▼
                  MCP Client Layer
                         │
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
 LinkedIn MCP      Gmail MCP      Browser MCP
        │                │                │
        ▼                ▼                ▼
 LinkedIn API     Gmail API      Playwright
                         │
                         ▼
                  External Systems
```

---

# 5. MCP Components

The MCP layer consists of:

## MCP Client

Responsible for:

- Tool discovery
- Tool invocation
- Request formatting
- Response parsing

---

## MCP Server

Responsible for:

- Authentication
- API communication
- Context translation
- Error handling

Each external integration is implemented as an independent MCP server.

---

## Tool Registry

Maintains the list of available tools.

Example:

- LinkedIn Search
- Gmail Send
- Calendar Create Event
- Browser Navigate
- GitHub Read Repository

---

## Authentication Manager

Responsible for:

- OAuth
- API Keys
- Token refresh
- Secret retrieval

---

## Context Adapter

Converts platform-specific responses into normalized data structures.

Example:

LinkedIn Job → Normalized Job Schema

Workday Job → Normalized Job Schema

Greenhouse Job → Normalized Job Schema

---

# 6. MCP Servers

The platform initially supports the following MCP servers.

| MCP Server | Purpose |
|------------|---------|
| Browser | Browser automation |
| Filesystem | Resume access |
| PostgreSQL | Structured queries |
| Google Drive | Resume storage |
| Gmail | Email |
| Google Calendar | Interview scheduling |
| GitHub | Portfolio analysis |
| LinkedIn | Job discovery |
| Greenhouse | Job applications |
| Lever | Job applications |
| Workday | Job applications |
| Notion | Career notes (future) |

---

# 7. Standard Tool Interface

Every MCP tool exposes the following interface.

### Metadata

- Tool Name
- Description
- Version
- Authentication
- Input Schema
- Output Schema

### Input

```json
{
  "parameters": {}
}
```

### Output

```json
{
  "status": "SUCCESS",
  "result": {},
  "metadata": {}
}
```

---

# 8. Tool Discovery

Agents discover tools dynamically.

Example:

```text
Resume Agent

↓

Discover Available Tools

↓

Filesystem

↓

PDF Parser

↓

Embedding Generator
```

The agent should not hardcode tool locations.

---

# 9. Authentication

Supported authentication mechanisms include:

- OAuth 2.0
- API Keys
- Service Accounts
- Session Cookies (Browser MCP only)

Credentials are stored in the platform's secret management system.

No credentials are stored within AI agents.

---

# 10. Context Normalization

Every MCP server converts provider-specific responses into a common platform schema.

Example:

LinkedIn

↓

LinkedIn Job JSON

↓

Normalized Job Schema

↓

Job Discovery Component

This keeps downstream services provider-agnostic.

---

# 11. Error Handling

Each MCP server distinguishes:

- Authentication Error
- Permission Error
- Validation Error
- Rate Limit
- Timeout
- Network Error
- Service Unavailable

Errors should be returned in a structured format.

---

# 12. Retry Policy

Retryable:

- Timeout
- Temporary network issues
- HTTP 429
- HTTP 503

Non-retryable:

- Invalid credentials
- Invalid request
- Permission denied

Retries use exponential backoff.

---

# 13. Browser MCP

The Browser MCP provides automation capabilities.

Responsibilities:

- Navigate
- Click
- Fill forms
- Upload files
- Capture screenshots
- Wait for elements
- Extract page content

Browser automation is isolated from business logic.

---

# 14. LinkedIn MCP

Responsibilities:

- Search jobs
- Read job descriptions
- Read company information

Limitations:

The implementation must comply with LinkedIn's applicable terms, authentication requirements, and technical restrictions. Where direct API access is unavailable or restricted, supported alternatives or user-authorized browser workflows should be used.

---

# 15. Gmail MCP

Responsibilities:

- Send email
- Read email (authorized)
- Track recruiter responses
- Generate drafts

---

# 16. Calendar MCP

Responsibilities:

- Create interview events
- Update interview schedule
- Delete events
- Retrieve upcoming interviews

---

# 17. GitHub MCP

Responsibilities:

- Read repositories
- Read README files
- Analyze portfolio
- Retrieve contribution history (where authorized)

---

# 18. PostgreSQL MCP

Responsibilities:

- Execute approved queries
- Read structured information
- Store AI metadata
- Retrieve workflow state

Write operations should be restricted according to platform policy.

---

# 19. Filesystem MCP

Responsibilities:

- Read resumes
- Read cover letters
- Read attachments
- Store generated documents

---

# 20. MCP Security

Requirements:

- OAuth where available
- Least-privilege access
- Token rotation
- Audit logging
- Request validation
- Permission checks

Every MCP request should be traceable.

---

# 21. Observability

Capture:

- Tool usage
- Latency
- Failure rate
- Success rate
- Authentication failures
- Token refreshes
- Rate limits
- Provider errors

---

# 22. Scalability

MCP servers are independently deployable.

Examples:

- Scale Browser MCP separately.
- Scale LinkedIn MCP independently.
- Scale Gmail MCP independently.

No MCP server should depend on another MCP server.

---

# 23. Future MCP Servers

Potential additions:

- Slack
- Microsoft Teams
- Discord
- Salesforce
- HubSpot
- Jira
- Confluence
- Dropbox
- OneDrive
- Box
- Azure DevOps

The architecture should support new MCP servers without requiring changes to AI agents.

---

# 24. Related Documents

- 02.05 AI Agent Layer
- 02.06 ACP Architecture
- 02.08 Event-Driven Architecture
- 05-mcp/*
- 07-api/*