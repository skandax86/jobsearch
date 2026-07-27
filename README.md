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

# 4. Apply database migrations
make migrate

# 5. Run API (terminal 1)
make api

# 6. Run web (terminal 2)
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
| 2 | Database schema + migrations | ✅ |
| 3 | Auth (identity domain) | ✅ |
| 4 | Resume upload + storage | ✅ |
| 5 | Resume parsing pipeline | ✅ |
| 6 | Job discovery | ✅ (demo + Remotive + optional Naukri) |
| 7 | Job matching / scoring | ✅ |
| 8 | LinkedIn personal connect + MCP + Job Discovery agent | ✅ |

## Cursor MCP (optional)

Personal job-board tools in Cursor (not app SSO). Config: `.cursor/mcp.json`

| Server | Purpose |
|--------|---------|
| `microsoft-learn` | LinkedIn/Microsoft API docs |
| `mcp-server-linkedin` | Your LinkedIn browser session (`uvx` + `--login`) |
| `naukri-mcp` | Naukri search / apply / resume tailor ([Naukri-MCP](https://github.com/sanjeev-txt/Naukri-MCP)) |

**Naukri in the web app (Discover):**

```bash
make naukri-mcp-setup
# fill NAUKRI_EMAIL / NAUKRI_PASSWORD in .env.naukri
cd apps/api && . .venv/bin/activate && pip install -e '.[naukri]' && playwright install chromium
```

Then on the dashboard enable the **Naukri** checkbox and click Discover (uses location / experience / skills filters).

**LinkedIn (Cursor only for now):**

```bash
uvx mcp-server-linkedin@latest --login
```

⚠️ Browser automation against LinkedIn/Naukri can risk account restriction. Use sparingly; never commit `.env.naukri`.

See `docs/` for full architecture and domain specifications.
