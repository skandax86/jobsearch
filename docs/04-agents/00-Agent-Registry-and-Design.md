# Agent Registry and Design

**Document ID:** 04.00  
**Status:** Draft

## Purpose

Defines the production registry for specialized CareerPilot AI agents. Common runtime requirements are in [AI Agent Layer](../02-architecture/05-AI-Agent-Layer.md); this document defines business responsibilities.

## Common Contract

Every agent receives a typed ACP task, authorized context references, constraints, and policy. It returns structured `result`, `confidence`, `warnings`, provenance, tool usage, and an outcome code. Agents do not write domain data, call other agents, or access providers directly.

## Registry

| Agent | Responsibility | Input | Output | Approval boundary |
|---|---|---|---|---|
| Planner | selects permitted workflow steps | user intent, policy | workflow plan | no side effects |
| Supervisor | monitors and recovers workflows | workflow state | route/retry/escalation | pauses unsafe work |
| Resume Analyzer | source resume → extraction proposal | document | canonical JSON proposal | facts need review |
| Job Discovery | finds normalized postings | preferences | job-source observations | provider policy |
| Ranking | scores eligible postings | profile, jobs | ranked matches + rationale | none |
| Resume Optimizer | tailors verified content | resume, job | JSON proposal | factual changes require approval |
| Cover Letter | drafts job-specific letter | verified profile, job | draft | send/use requires approval |
| Application | prepares/submits authorized application | approved package | submission evidence | submission policy |
| Tracker | reconciles status | emails/provider evidence | status proposal | ambiguity escalates |
| Interview Coach | creates prep plan | interview, company, profile | preparation content | none |
| Career Coach | creates recommendations | feedback, profile, market signals | recommendations | none |
| Notification | sends approved notices | event, preferences | delivery result | channel policy |

## Agent Quality Rules

- Use schema-constrained outputs and validate before downstream use.
- Cite input provenance in explanations where practicable.
- Enforce a task-specific token, tool-call, latency, and retry budget.
- Return uncertainty rather than guessing.
- Emit execution telemetry and safe audit records.

## Acceptance Criteria

Each agent has a typed contract, prompt version, test fixture, evaluation metrics, access policy, failure policy, and human escalation condition before production enablement.

## Related Documents

- [06-ACP-Architecture.md](../02-architecture/06-ACP-Architecture.md)
- [07-MCP-Architecture.md](../02-architecture/07-MCP-Architecture.md)
- [00-Prompt-Management.md](../09-prompts/00-Prompt-Management.md)
