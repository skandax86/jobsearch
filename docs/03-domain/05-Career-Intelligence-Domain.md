# Career Intelligence Domain

**Document ID:** 03.05  
**Status:** Draft

## Purpose

Defines derived, explainable insights: job matches, skill gaps, market signals, learning suggestions, and career recommendations.

## Rules

- All outputs are derived and versioned; they never overwrite verified candidate facts.
- A `JobMatch` records profile/resume version, job snapshot, scoring model version, feature values, explanation, and confidence.
- Recommendations distinguish facts, inferred signals, and user action suggestions.
- Feedback such as save, dismiss, apply, interview, and offer is captured for evaluation, not silently treated as ground truth.

## Events

`JobMatched`, `SkillGapIdentified`, `CareerRecommendationGenerated`, `RecommendationFeedbackRecorded`.

## Related Documents

- [02-Candidate-Domain.md](02-Candidate-Domain.md)
- [03-Job-and-Company-Domain.md](03-Job-and-Company-Domain.md)
- [AI Evaluation](../12-testing/01-AI-Evaluation.md)
