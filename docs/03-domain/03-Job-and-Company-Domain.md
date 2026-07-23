# Job and Company Domain

**Document ID:** 03.03  
**Status:** Draft

## Purpose

Defines ingestion, normalization, provenance, deduplication, eligibility, and lifecycle for job postings and companies.

## Aggregates

- `Company`: canonical organization identity, industry, website, and enrichment provenance.
- `JobPosting`: normalized role, description snapshot, location, compensation, requirements, source state, and expiry.
- `JobSource`: provider-specific observation, source URL/ID, retrieval timestamp, and raw payload reference.

## Rules

- Preserve source observations; deduplication merges into a canonical posting without destroying provenance.
- Job-derived claims such as salary, sponsorship, and remote status retain confidence and source evidence.
- A posting is ineligible when it violates a candidate's explicit hard constraints; matching is a derived, separate domain.
- Expired, closed, or changed postings remain historically traceable.

## Events

`JobDiscovered`, `JobNormalized`, `JobDeduplicated`, `JobUpdated`, `JobExpired`, `CompanyEnriched`.

## Related Documents

- [04-Application-and-Interview-Domain.md](04-Application-and-Interview-Domain.md)
- [06-ACP-Architecture.md](../02-architecture/06-ACP-Architecture.md)
- [07-MCP-Architecture.md](../02-architecture/07-MCP-Architecture.md)
