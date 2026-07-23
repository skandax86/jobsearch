# ACP Architecture

**Document ID:** 02.06

**Version:** 1.0

**Status:** Draft

**Last Updated:** 2026-07-12

---

# 1. Purpose

This document defines how AI agents communicate, coordinate, collaborate, and execute workflows using the Agent Communication Protocol (ACP).

ACP is the internal communication backbone of CareerPilot AI.

It enables multiple autonomous AI agents to work together while remaining loosely coupled, observable, and independently deployable.

ACP is responsible for agent-to-agent communication.

ACP is **not** responsible for:

- External API access
- Database operations
- Browser automation
- Authentication

These responsibilities belong to MCP and the platform services.

---

# 2. Goals

ACP should:

- Coordinate multiple AI agents.
- Execute long-running workflows.
- Support parallel execution.
- Handle retries.
- Support human approval checkpoints.
- Provide workflow observability.
- Maintain execution state.
- Enable fault recovery.

---

# 3. ACP Principles

ACP follows these principles.

## Loose Coupling

Agents never call each other directly.

All communication occurs through ACP.

---

## Stateless Communication

Messages contain all information required for execution.

Agents should not depend on another agent's internal memory.

---

## Workflow Driven

ACP executes workflows.

Agents execute tasks.

Agents do not own workflow logic.

---

## Event-Based

Communication is asynchronous whenever possible.

---

## Deterministic Routing

ACP decides which agent receives a task.

Agents never self-dispatch work.

---

# 4. ACP Architecture

```text
                  API Service
                       │
                       ▼
              ACP Orchestrator
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
 Resume Agent   Search Agent   Ranking Agent
        │              │              │
        └──────────────┼──────────────┘
                       ▼
              Workflow State Store
                       │
                       ▼
                  Event Bus
```

---

# 5. ACP Components

## Workflow Engine

Responsible for:

- Workflow execution
- State transitions
- Parallel execution
- Retry policies
- Timeout handling

Technology:

LangGraph

---

## Orchestrator

Responsible for:

- Task assignment
- Agent scheduling
- Dependency resolution
- Human approval
- Workflow completion

---

## Message Router

Routes messages to the correct agent.

Supports:

- Broadcast
- Direct messages
- Workflow events
- Retry messages

---

## State Manager

Stores workflow execution state.

Tracks:

- Current step
- Previous results
- Retry count
- Execution history
- Human approval state

---

## Event Publisher

Publishes workflow events.

Examples:

ResumeParsed

JobsFound

ResumeOptimized

ApplicationSubmitted

WorkflowCompleted

---

## Approval Manager

Responsible for:

- User approvals
- Resume edits
- Application confirmation
- Email confirmation

ACP pauses until approval is received.

---

# 6. Workflow Lifecycle

```text
Workflow Created

↓

Task Planned

↓

Agent Selected

↓

Agent Executed

↓

Result Validated

↓

Next Task

↓

Approval (optional)

↓

Workflow Completed
```

---

# 7. Standard ACP Message

Every message must contain:

```json
{
  "message_id": "...",
  "workflow_id": "...",
  "correlation_id": "...",
  "sender": "...",
  "receiver": "...",
  "task_type": "...",
  "priority": "...",
  "status": "...",
  "payload": {},
  "metadata": {},
  "timestamp": "..."
}
```

---

# 8. Workflow States

```text
Created

Queued

Running

Waiting

Approved

Rejected

Completed

Failed

Cancelled

Timed Out
```

---

# 9. Agent Communication

Agents communicate only through ACP.

Example:

```text
Planner Agent

↓

Search Agent

↓

Ranking Agent

↓

Resume Agent

↓

Cover Letter Agent

↓

Application Agent

↓

Notification Agent
```

No direct agent-to-agent communication is allowed.

---

# 10. Parallel Execution

ACP supports parallel execution.

Example:

```text
Planner

↓

────────────────────────────

Resume Optimization

Company Research

Interview Preparation

Skill Analysis

────────────────────────────

↓

Merge Results

↓

Next Workflow Step
```

Parallel execution reduces overall workflow time.

---

# 11. Retry Strategy

Retryable failures include:

- MCP timeout
- LLM timeout
- Network interruption
- Temporary rate limiting

Non-retryable failures include:

- Invalid resume
- Authentication failure
- User rejection
- Business rule violation

Retries use exponential backoff.

---

# 12. Human Approval

ACP supports workflow pause points.

Examples:

- Resume modification
- Cover letter generation
- Job application
- Recruiter outreach
- Calendar scheduling

Workflow state is persisted while waiting.

---

# 13. Workflow Examples

## Resume Upload

```text
Resume Upload

↓

Resume Agent

↓

Candidate Profile

↓

Store Resume

↓

Workflow Complete
```

---

## Job Search

```text
Planner

↓

Search Agent

↓

Ranking Agent

↓

Recommendation Agent

↓

Workflow Complete
```

---

## Auto Apply

```text
Planner

↓

Resume Optimizer

↓

Cover Letter

↓

Approval

↓

Application Agent

↓

Notification

↓

Complete
```

---

# 14. Error Handling

ACP distinguishes:

- Agent Failure
- Tool Failure
- Validation Failure
- Timeout
- Cancellation
- Human Rejection

Each failure has its own recovery policy.

---

# 15. Workflow Persistence

ACP stores:

- Workflow ID
- Current Step
- Completed Steps
- Agent Outputs
- Retry Count
- Execution Time
- Approval State

This enables workflow recovery after service restarts.

---

# 16. Observability

Track:

- Workflow duration
- Agent latency
- Retry count
- Success rate
- Failure reason
- Queue time
- Human approval delay

All workflow executions are traceable end-to-end.

---

# 17. Security

ACP validates:

- Workflow permissions
- User ownership
- Agent authorization
- Message integrity

Sensitive payloads should not be logged.

---

# 18. Scalability

ACP supports:

- Multiple orchestrators
- Distributed workers
- Queue-based execution
- Independent agent scaling

Workflows are designed to execute across multiple nodes.

---

# 19. Future Enhancements

Future ACP capabilities may include:

- Dynamic workflow generation
- Multi-user collaborative workflows
- Workflow templates
- Agent voting
- Self-healing workflows
- Adaptive execution strategies

---

# 20. Related Documents

- 02.05 AI Agent Layer
- 02.07 MCP Architecture
- 02.08 Event-Driven Architecture
- 04-agents/*
- workflows/*