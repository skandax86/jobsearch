# ACP Messages

Typed envelopes exchanged during workflow execution.

| File | Purpose |
|------|---------|
| [task-request.json](./task-request.json) | Example task dispatch |
| [task-result.json](./task-result.json) | Example agent result envelope |

Schemas: [`../schemas/message.schema.json`](../schemas/message.schema.json)

## Envelope rules

- Prefer **references** (`payload_ref`) over large PII blobs when possible.
- `attempt` increments on retry.
- `receiver` is an agent id from `agents/` registry.
- Results must include `confidence` (0–1) when the agent proposes structured facts.
