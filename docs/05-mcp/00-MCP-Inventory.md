# MCP Inventory

**Document ID:** 05.00  
**Status:** Draft

## Purpose

Defines the external capabilities exposed to CareerPilot agents through MCP. MCP is the integration boundary; agents request capabilities, while server adapters manage provider-specific authentication, limits, normalization, and errors.

## Initial Servers

| Capability | MCP server | Allowed tools | Data/side-effect policy |
|---|---|---|---|
| Resume files | storage/filesystem | read source, retrieve render, store artifact | user-scoped only |
| Job discovery | job-search | search, retrieve posting | read-only; provider terms apply |
| ATS/application | ats/browser | inspect form, draft/submit approved package | side effects require policy/approval |
| Email | gmail | search, draft, send approved message | OAuth and scope minimum |
| Calendar | calendar | read availability, create approved event | OAuth and explicit consent |
| Portfolio | github | read public/authorized repositories | read-only |
| LinkedIn | linkedin | connection status, OpenID profile, job search (partner-gated) | OAuth OpenID; Jobs API unsupported without partner access |
| Data access | domain API adapter | authorized domain reads | agents never receive broad SQL access |

## Contract Rules

Every tool has JSON input/output schemas, explicit OAuth/API-key scopes, timeout and retry classification, rate-limit policy, audit event, and normalized error codes. Tool responses contain provider evidence and never expose secrets.

## Provider Policy

Use official APIs where available. Browser workflows are isolated, user-authorized, rate-limited, and must comply with applicable platform terms. CAPTCHA, MFA, or ambiguous outcomes pause for the user rather than attempting circumvention.

## Related Documents

- [07-MCP-Architecture.md](../02-architecture/07-MCP-Architecture.md)
- [13-Security-Architecture.md](../02-architecture/13-Security-Architecture.md)
