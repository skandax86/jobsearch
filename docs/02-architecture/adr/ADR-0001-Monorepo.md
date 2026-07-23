// ... existing code relating to Monorepo decision and initial justification ...

## Synergy with Deployed Architecture (Monolith vs. Service Boundaries)

While the codebase resides in a unified Monorepo structure, it is critical to distinguish between:
1.  **The Source Tree:** The single, cohesive repository containing all domain code (API handlers, Worker scripts, Shared Models).
2.  **The Deployed Artifacts:** The independently versioned and containerized services (e.g., `FastAPI Gateway`, `Worker Queue Consumer`, `Frontend Client`) that communicate via defined contracts (Protocols).

**Implication:** The Monorepo enforces strong contract integrity. Any change to a shared domain model (e.g., a Pydantic schema representing a Job object) can be atomically tested across all layers—API ingress, database persistence, and worker consumer logic—before deployment. This minimizes deployment risk associated with cross-service contract drift.

// ... rest of Monorepo ADR conclusion or appendices ...