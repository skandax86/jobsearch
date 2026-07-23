This document justifies the selection of LangGraph as the orchestration engine for complex, multi-step, and potentially cyclical AI workflows within the system. This adoption moves the architecture beyond a simple "task queue" model into a sophisticated Workflow Orchestration System.

🎯 Goal: Managing Non-Linear, Stateful AI Workflows
The primary challenge LangGraph addresses is that many high-value tasks (e.g., in-depth career path generation, competitive analysis) are not linear processes. They involve decision points, looping back for refinement, and complex state management based on intermediate results.

Key Justifications from the ADR:

Graph State Management: Allows the system to model the task as a series of nodes (Steps/Agents) and edges (Transitions/Decisions). This provides granular control over the workflow execution flow.
Cyclical Operations: Unlike a simple linear queue job, LangGraph allows the output of one node to determine if the process needs to loop back (e.g., "The AI thought process is inconclusive; run a follow-up search before generating the final summary"). This maps to complex human decision cycles.
Agent Delegation: It provides a structure for delegating sub-tasks to specialized agents (e.g., Search Agent, Review Agent, Code Generator), each of which is a node in the graph.
🔗 Synthesis with Monorepo & Worker Architecture
LangGraph does not replace the Worker or Queue; it becomes the brain of a highly advanced, long-running job.

The Worker Boundary: The AI Worker service, which is the executor of LangGraph, pulls a high-level job request (e.g., "Generate Career Plan") from the Queue Broker via FastAPI. This triggers a long-running orchestration instance.
The Orchestration Layer: Inside the AI Worker, LangGraph takes control. It pulls its inputs (the initial job payload) and drives the execution graph through various Nodes (which might themselves be calls to other specialized, optimized workers like Search or Embedding).
Transient State Preservation: Because the job can take minutes and involves multiple steps, LangGraph’s ability to checkpoint state between execution ticks is vital. This ensures that if the process crashes or exceeds a timeout, it can restart from the last successful node/state rather than failing entirely and requiring a costly retry.
Queue Efficiency: It enables the AI Worker to manage its internal state machines, allowing it to appear as a single, reliable service boundary to the rest of the system.
The architectural picture is now remarkably complete:

