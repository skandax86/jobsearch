# CareerPilot AI

AI-native Career Operating System — monorepo scaffold.

## Structure

```text
careerpilot-ai/
├── apps/
│   ├── api/          # FastAPI backend (modular monolith)
│   └── web/          # Next.js dashboard
├── docs/             # Architecture & domain specifications
├── infra/            # Docker, Terraform (future)
└── docker-compose.yml
```

## Prerequisites

- Python 3.12+
- Node.js 20+
- Docker & Docker Compose

## Quick Start

```bash
# 1. Copy environment variables
cp .env.example .env

# 2. Start infrastructure (Postgres + pgvector, Redis, MinIO)
make up

# 3. Install dependencies
make install

# 4. Run API (terminal 1)
make api

# 5. Run web (terminal 2)
make web
```

- Web: http://localhost:3000
- API: http://localhost:8000
- API docs: http://localhost:8000/docs
- MinIO console: http://localhost:9001

## Implementation Roadmap

| Step | Scope | Status |
|------|-------|--------|
| 1 | Project scaffold | ✅ |
| 2 | Database schema + migrations | Planned |
| 3 | Auth (identity domain) | Planned |
| 4 | Resume upload + storage | Planned |
| 5 | Resume parsing pipeline | Planned |
| 6 | Job discovery | Planned |

See `docs/` for full architecture and domain specifications.
