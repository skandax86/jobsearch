# Testing Strategy

**Document ID:** 12.00  
**Status:** Draft

## Purpose

Defines the layered verification required before CareerPilot changes are released.

## Test Pyramid

| Level | Scope | Required examples |
|---|---|---|
| Unit | deterministic domain logic | state transitions, matching features, schema validation |
| Contract | boundaries | OpenAPI, ACP message, MCP tool, event schemas |
| Integration | service plus dependencies | PostgreSQL migrations, Redis queues, object storage adapters |
| Workflow | ACP graphs | approval pause/resume, retry, compensation, idempotency |
| End-to-end | user journey | upload → review → render → approved application preparation |
| Security | adversarial controls | authorization, secret leakage, upload validation, prompt injection |
| Evaluation | AI quality | structured output, truthfulness, ranking quality, render quality |

## Rules

- Every defect gets a regression test at the lowest practical level.
- Use anonymized/synthetic resumes and job descriptions in test fixtures.
- Browser automation runs only against permitted test sites or controlled fixtures in CI.
- Test migrations for forward and rollback compatibility; never use production PII.
- Gate releases on agreed critical tests, schema compatibility, and security scanning.

## Related Documents

- [16-Failure-Recovery.md](../02-architecture/16-Failure-Recovery.md)
- [00-Agent-Registry-and-Design.md](../04-agents/00-Agent-Registry-and-Design.md)
