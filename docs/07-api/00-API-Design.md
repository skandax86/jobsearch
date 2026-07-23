# API Design

**Document ID:** 07.00  
**Status:** Draft

## Purpose

Defines public and internal API rules. Detailed routes are generated from FastAPI OpenAPI contracts; this document governs the shape, compatibility, authorization, and asynchronous behavior of those contracts.

## API Surfaces

| Surface | Consumers | Authentication | Purpose |
|---|---|---|---|
| Public client API `/api/v1` | web, extension, future mobile | user session/OAuth token | user-facing commands and reads |
| Internal service API | services/workers | service identity | domain collaboration |
| Agent/workflow API | ACP and workers | scoped workload identity | authorized snapshots and result persistence |
| Webhooks | approved partners | signed requests | asynchronous notifications |

## Rules

- Version breaking public changes under a new `/vN` route.
- Use resource-oriented routes and typed Pydantic schemas.
- Return `{data, metadata, errors, request_id}`; use RFC-style problem details for errors where practical.
- Persist an asynchronous command before returning `202 Accepted`, with a workflow/resource URL for status.
- Require idempotency keys for creation and external side-effect endpoints.
- Enforce object-level authorization in the domain service, not only at the gateway.

## Key Resources

`/me`, `/candidate-profile`, `/resumes`, `/jobs`, `/matches`, `/applications`, `/interviews`, `/workflows`, `/integrations`, `/notifications`, and `/exports`.

## Related Documents

- [12-API-Gateway.md](../02-architecture/12-API-Gateway.md)
- [00-ACP-Specification.md](../06-acp/00-ACP-Specification.md)
