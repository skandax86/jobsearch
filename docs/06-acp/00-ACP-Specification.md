# ACP Specification

**Document ID:** 06.00  
**Status:** Draft

## Purpose

Defines the application-level protocol for coordinating CareerPilot agents. ACP uses durable workflow state and typed messages; it complements MCP, which handles external tools.

## Message Contract

```json
{
  "message_id": "uuid",
  "workflow_id": "uuid",
  "correlation_id": "uuid",
  "sender": "planner",
  "receiver": "job_discovery",
  "task_type": "search_jobs",
  "attempt": 1,
  "deadline": "ISO-8601 timestamp",
  "payload_ref": "authorized-domain-reference",
  "policy_ref": "automation-policy-version"
}
```

Messages carry references rather than unnecessary PII. Results use the standard agent envelope and are persisted before the next transition.

## Lifecycle

`created → queued → running → waiting_for_approval → completed | failed | cancelled | timed_out`.

ACP owns routing, dependency ordering, retries, and approval pauses. The Planner produces only policy-valid plans; the Supervisor applies timeouts, budgets, failure recovery, and escalation.

## Required Controls

- idempotency for every task and side effect;
- bounded retries with backoff and a DLQ;
- explicit fan-out/fan-in join rules;
- approval tokens bound to workflow, action, and expiry;
- trace, audit, and version metadata on every transition.

## Related Documents

- [06-ACP-Architecture.md](../02-architecture/06-ACP-Architecture.md)
- [00-Agent-Registry-and-Design.md](../04-agents/00-Agent-Registry-and-Design.md)
