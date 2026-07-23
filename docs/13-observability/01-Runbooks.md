# Operations Runbooks

**Document ID:** 13.01  
**Status:** Draft

## Purpose

Provide the minimum operator procedures for high-impact production conditions. Each alert must link to its relevant runbook.

## Queue Backlog

1. Confirm queue depth, oldest-message age, consumer health, and provider error rate.
2. Pause non-critical scheduled work and scale the affected worker pool within resource limits.
3. Do not replay messages until idempotency and dependency status are confirmed.
4. Move exhausted messages to DLQ and reconcile user-visible workflow status.

## Application Submission Ambiguity

1. Stop automatic retry for the application.
2. Inspect provider confirmation evidence, status page, and application idempotency key.
3. Mark `submitted`, `not_submitted`, or `manual_review`; notify the user when required.
4. Preserve screenshots/evidence according to retention policy.

## LLM or MCP Provider Degradation

1. Check provider status, error class, rate limits, and circuit-breaker state.
2. Use an approved fallback only when model/tool policy permits it.
3. Queue non-urgent work; do not lower truthfulness or approval controls.
4. Recover/replay only safe idempotent tasks after stabilization.

## Database Recovery

1. Declare incident and stop unsafe writes if durability is uncertain.
2. Restore or fail over according to the documented RPO/RTO plan.
3. Validate migrations, outbox state, and workflow reconciliation before reopening writes.
4. Record affected workflows and communicate user impact.
