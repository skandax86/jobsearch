# AI Evaluation

**Document ID:** 12.01  
**Status:** Draft

## Purpose

Defines repeatable quality gates for agents, prompts, model changes, and resume rendering workflows.

## Evaluation Sets

Maintain versioned, consent-safe or synthetic datasets for resumes, job descriptions, application questions, and tool-error scenarios. Label expected schema, factual constraints, match relevance, and safety outcomes.

## Core Metrics

| Capability | Metrics |
|---|---|
| Resume extraction | field precision/recall, review rate, provenance coverage |
| Resume optimization | factual-consistency rate, keyword coverage, user acceptance, ATS render quality |
| Job ranking | precision@K, acceptance/save rate, downstream interview rate, explanation quality |
| Generation | schema-valid rate, human rating, policy violations, latency/cost |
| Agents/tools | task completion, retry rate, unsafe-action prevention, tool error handling |

## Release Rule

No model or prompt change reaches production without passing schema, safety, regression, and task-specific quality thresholds against a baseline. Store model, prompt, template, and dataset versions with results.

## Related Documents

- [00-Prompt-Management.md](../09-prompts/00-Prompt-Management.md)
- [01-Resume-Domain.md](../03-domain/01-Resume-Domain.md)
