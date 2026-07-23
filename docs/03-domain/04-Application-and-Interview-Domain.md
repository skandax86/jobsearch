# Application and Interview Domain

**Document ID:** 03.04  
**Status:** Draft

## Purpose

Defines the durable lifecycle for candidate applications, approvals, submission evidence, recruiter contact, and interviews.

## Application Aggregate

An `Application` references one candidate, normalized job posting, immutable application package, and status history. It is the only domain allowed to record a submission attempt.

```text
draft → preparing → awaiting_approval → approved → submitting → submitted
                                         │              │
                                      rejected      manual_review / failed
submitted → assessment → interview → offer / rejected / withdrawn
```

## Rules

- Submission requires an explicit approval or a matching user automation policy.
- Every submission stores provider confirmation, timestamp, job snapshot, resume render checksum, and idempotency key.
- Ambiguous browser outcomes enter `manual_review`; retrying cannot produce a duplicate application.
- Interview scheduling changes are auditable and require calendar authorization.

## Events

`ApplicationPrepared`, `ApplicationApproved`, `ApplicationSubmitted`, `ApplicationStatusUpdated`, `InterviewDetected`, `InterviewScheduled`.

## Related Documents

- [01-Resume-Domain.md](01-Resume-Domain.md)
- [16-Failure-Recovery.md](../02-architecture/16-Failure-Recovery.md)
