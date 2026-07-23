"// ... existing code defining FastAPI selection and initial benefits like Pydantic usage, automatic docs, and performance gains.

## Architectural Role: Contract Enforcement Layer (The Gatekeeper)
While FastAPI serves as the service ingress point, its critical function within this Monorepo/Worker stack is functioning as the **Quality of Service (QoS) and Contract Enforcement Layer.**

1.  **Ingress Validation:** By utilizing Pydantic models, FastAPI acts as the Gatekeeper, rigorously validating all incoming client payloads against the required system contract. This prevents malformed or incomplete requests from entering the business logic and, most importantly, polluting the high-cost asynchronous Worker queues.
2.  **Service Isolation:** It successfully isolates the client from the internal plumbing of the queue system, presenting a clean, synchronous API facade while reliably queuing asynchronous jobs.
3.  **Reliable Hand-off:** The successful passage of a request through the FastAPI layer guarantees that the resultant job payload possesses the required schema fidelity necessary for dependable, low-latency execution by downstream workers.

// ... rest of the ADR conclusion or appendices ..."