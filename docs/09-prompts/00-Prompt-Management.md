# Prompt Management

**Document ID:** 09.00  
**Status:** Draft

## Purpose

Defines how prompts are authored, versioned, evaluated, released, and observed. Prompts are production assets, not inline strings.

## Prompt Contract

Every prompt declares an ID, semantic version, owner, purpose, allowed variables, required context references, output JSON schema, model constraints, safety constraints, evaluation dataset, and rollback version.

## Rules

- Store prompts as versioned files under `packages/prompts`, not inside agents.
- Pass structured context and explicit schemas; do not rely on free-form formatting.
- Keep role, policy, task, context, and output instructions separate.
- Redact sensitive content from traces by default.
- Release prompt changes through evaluation and a feature flag; retain prior versions for reproducibility.
- A prompt may propose resume content but cannot generate raw renderer markup or factual claims without sources.

## Lifecycle

`draft → evaluated → approved → staged → active → deprecated`.

## Related Documents

- [05-AI-Agent-Layer.md](../02-architecture/05-AI-Agent-Layer.md)
- [00-Testing-Strategy.md](../12-testing/00-Testing-Strategy.md)
