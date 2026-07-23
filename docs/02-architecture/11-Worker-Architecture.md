# Worker Architecture

**Document ID:** 02.11

**Version:** 1.0

**Status:** Draft

**Last Updated:** 2026-07-12

---

# 1. Purpose

This document defines the Worker Architecture of CareerPilot AI.

Workers are responsible for executing asynchronous, long-running, computationally expensive, and background tasks that should not block user-facing API requests.

The Worker Layer enables scalability, resiliency, and efficient resource utilization by separating request processing from background execution.

---

# 2. Goals

The Worker Architecture should:

- Keep APIs responsive.
- Execute asynchronous tasks.
- Support retries.
- Enable horizontal scaling.
- Support scheduled jobs.
- Support event-driven execution.
- Handle long-running AI workflows.
- Recover safely from failures.

---

# 3. Design Principles

Workers must be:

- Stateless
- Idempotent
- Independently deployable
- Queue-driven
- Observable
- Retryable
- Horizontally scalable

Workers should never expose public APIs.

---

# 4. High-Level Architecture

```text
                   User
                    │
                    ▼
               API Service
                    │
          Publish Background Job
                    │
                    ▼
               Queue Broker
                    │
      ┌─────────────┼─────────────┐
      ▼             ▼             ▼
 Resume Worker  AI Worker  Browser Worker
      │             │             │
      ▼             ▼             ▼
 PostgreSQL      MCP         External APIs
```

---

# 5. Worker Categories

The platform consists of multiple worker types.

| Worker | Responsibility |
|----------|----------------|
| Resume Worker | Resume parsing |
| Resume Renderer Worker | LaTeX, DOCX, and HTML rendering and validation |
| AI Worker | AI agent execution |
| Search Worker | Job discovery |
| Ranking Worker | Job ranking |
| Browser Worker | Browser automation |
| Notification Worker | Email & notifications |
| Analytics Worker | Metrics generation |
| Scheduler Worker | Periodic jobs |
| Cleanup Worker | Maintenance |
| Embedding Worker | Vector generation |

---

# 6. Resume Worker

Responsibilities:

- Parse PDFs
- Parse DOCX
- OCR (future)
- Metadata extraction
- Resume normalization
- Candidate profile generation

Triggered by:

ResumeUploaded

---

# 7. AI Worker

Responsibilities:

- Execute ACP workflows
- Run AI agents
- Generate cover letters
- Optimize resumes
- Generate interview questions

AI workers are compute-intensive and scale independently.

---

# 7.1 Resume Renderer Worker

Responsibilities:

- Render approved canonical Resume JSON through versioned templates.
- Compile LaTeX to text-selectable PDF in an isolated sandbox.
- Generate editable DOCX and preview/print-ready HTML.
- Validate output type, text extraction, checksum, and required sections.

Renderer workers do not call LLMs and do not alter content. They are idempotent for the content, template, renderer, and render-option versions.

---

# 8. Search Worker

Responsibilities:

- Crawl job boards
- Execute MCP searches
- Normalize jobs
- Remove duplicates
- Enrich company information

Triggered by:

JobSearchRequested

---

# 9. Browser Worker

Technology:

Playwright

Responsibilities:

- Easy Apply
- ATS forms
- File uploads
- Login sessions
- Screenshot capture

Browser workers are isolated for security and resource management.

---

# 10. Embedding Worker

Responsibilities:

- Generate embeddings
- Update vector database
- Refresh embeddings
- Similarity indexing

Triggered by:

- ResumeParsed
- JobDiscovered
- CandidateUpdated

---

# 11. Notification Worker

Responsibilities:

- Email
- Push notifications
- In-app notifications
- Reminder generation

Triggered by:

ApplicationSubmitted

InterviewScheduled

WorkflowCompleted

---

# 12. Analytics Worker

Responsibilities:

- KPI generation
- User metrics
- Conversion funnels
- AI usage statistics
- Daily reports

Runs on scheduled intervals and consumes business events.

---

# 13. Scheduler Worker

Responsibilities:

Execute recurring jobs.

Examples:

- Refresh job listings
- Resume embedding refresh
- Cleanup expired sessions
- Daily analytics
- Health checks

---

# 14. Cleanup Worker

Responsibilities:

- Delete expired cache
- Remove temporary files
- Archive completed workflows
- Remove stale browser sessions

Runs on configurable schedules.

---

# 15. Queue Architecture

```text
API

↓

Queue

↓

Worker

↓

Business Logic

↓

Database

↓

Event

↓

Next Worker
```

Workers never communicate directly.

Communication occurs through:

- Events
- Queues
- ACP

---

# 16. Queue Design

Example queues:

```
resume.parse

resume.embedding

job.discovery

job.ranking

application.submit

browser.automation

notification.email

analytics.daily

cleanup

scheduler
```

Each queue is independently scalable.

---

# 17. Job Lifecycle

```text
Job Created

↓

Queued

↓

Worker Picks Job

↓

Executing

↓

Success

or

Retry

or

Dead Letter Queue
```

---

# 18. Retry Strategy

Retryable:

- Network failure
- MCP timeout
- Rate limit
- Temporary provider outage

Non-Retryable:

- Invalid resume
- Invalid payload
- User permission error
- Authentication failure

Retries use exponential backoff with jitter.

---

# 19. Dead Letter Queue

Jobs exceeding retry limits move to the DLQ.

Examples:

- Invalid payload
- Corrupted resume
- Permanent MCP failure

DLQ jobs should be visible in monitoring dashboards.

---

# 20. Concurrency

Workers should support concurrent execution.

Examples:

- Multiple resumes parsed simultaneously.
- Multiple browser sessions.
- Parallel AI workflows.
- Independent embedding generation.

Concurrency limits should be configurable.

---

# 21. Resource Isolation

Separate worker pools for:

- Browser Automation
- AI Inference
- Resume Parsing
- Notifications
- Analytics

Heavy workloads should not impact lightweight tasks.

---

# 22. Scheduling

Support:

- Cron jobs
- Delayed jobs
- Recurring jobs
- Event-triggered jobs

Future support:

Dynamic scheduling.

---

# 23. Monitoring

Track:

- Queue depth
- Processing time
- Retry count
- Worker utilization
- Failure rate
- Success rate
- Queue latency

Workers expose health and readiness endpoints where applicable.

---

# 24. Scaling Strategy

Scale worker pools independently.

Examples:

High application traffic:

Increase Browser Workers.

Large resume imports:

Increase Resume Workers.

Large AI workloads:

Increase AI Workers.

Scaling decisions should be driven by queue metrics.

---

# 25. Security

Workers operate with least-privilege credentials.

Sensitive information:

- Never logged
- Never hardcoded
- Retrieved from secret management

Browser workers execute in isolated environments.

---

# 26. Future Enhancements

Future worker types:

- Salary Intelligence Worker
- Recruiter Discovery Worker
- Company Intelligence Worker
- Learning Recommendation Worker
- Skill Gap Worker
- Market Intelligence Worker

---

# 27. Related Documents

- 02.08 Event-Driven Architecture
- 02.09 Data Layer
- 02.10 Storage Layer
- 02.12 API Gateway
- 06 ACP Architecture
