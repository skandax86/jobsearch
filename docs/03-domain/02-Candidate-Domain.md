# Candidate Domain

**Document ID:** 03.02  
**Status:** Draft

## Purpose

Defines the verified professional profile and job-search preferences owned by a user. It is separate from source resume documents and from AI-generated recommendations.

## Aggregate

`CandidateProfile` owns verified facts: identity details, work history references, skills, education, work authorization, and candidate-controlled preferences. `PreferenceSet` owns roles, locations, compensation, remote policy, blocked companies, and automation limits.

## Rules

- Facts require a user source or explicit confirmation.
- Recommendations and inferred skills are stored separately with confidence and provenance.
- Preferences are user-controlled and versioned for workflows.
- A workflow uses a snapshot of the preference version that started it.

## Events

`CandidateProfileUpdated`, `CandidateFactVerified`, `PreferencesUpdated`, `AutomationPolicyUpdated`.

## Interfaces

Candidate Service exposes profile read/update, fact confirmation, preference management, and read-only profile snapshots for authorized workflows. It never lets agents modify verified facts directly.

## Related Documents

- [00-Domain-Overview.md](00-Domain-Overview.md)
- [01-Resume-Domain.md](01-Resume-Domain.md)
- [03-Job-and-Company-Domain.md](03-Job-and-Company-Domain.md)
