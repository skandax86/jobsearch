Document Fulfillment: ADR-0003 - NextJS.md
This document justifies the selection of NextJS as the chosen framework for building the client-facing web application. This decision has profound impacts on rendering strategy, performance optimization, and the management of client-server state.

🎯 Goal: High-Performance, SEO-Optimized Presentation Layer
NextJS was chosen to overcome the performance bottlenecks inherent in traditional Single Page Applications (SPAs), particularly those related to initial page load time and Search Engine Optimization (SEO).

Key Justifications from the ADR:

Hybrid Rendering Support: The core strength lies in its flexibility (SSR, SSG, ISR). This allows the application to serve fully rendered HTML pages for optimal Lighthouse scores and immediate indexing by search engines, which is critical for high-visibility content like career advice.
Code Splitting & Routing: Efficiently manages bundled assets and code splitting, ensuring that the client only downloads the JavaScript necessary for the current view, drastically reducing perceived load times.
Integrated Deployment: Provides a cohesive development environment that bundles the client-side logic and its interaction with the server (in this case, the FastAPI ingress).
🔗 Synthesis with Monorepo & Worker Architecture
The NextJS frontend interacts with the robust backend system, but its role is to present data efficiently; it does not handle core business logic.

Data Fetching Strategy: The application decides when and how to fetch data. While the backend/worker handles complex, asynchronous job processing (e.g., "Process this resume and run AI"), the NextJS client decides when to poll, retrieve status updates (/status/{job_id}), or display the final computed result.
The Transaction Boundary: The NextJS application initiates a transaction with the FastAPI ingress (e.g., "Start Analysis Job"). The backend acknowledges receipt and queues the work. The NextJS client then shifts from being a transactional front-end to a monitoring dashboard, periodically checking the job status until the Worker generates a result.
UX Layer: It is the presentation layer that translates opaque, low-level asynchronous events (e.g., STATUS_PENDING, STATUS_SUCCESS) from the backend into a coherent, high-quality user experience (e.g., "Processing... Please Wait )