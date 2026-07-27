# CareerPilot API

FastAPI backend service for CareerPilot AI.

## Local setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

From the monorepo root (with Docker infra running):

```bash
make migrate   # apply Alembic migrations
make api       # uvicorn on :8000
```

## Auth

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/auth/register` | Create user + candidate profile + session |
| POST | `/api/v1/auth/login` | Authenticate and issue session |
| POST | `/api/v1/auth/logout` | Revoke session |
| GET | `/api/v1/me` | Current user (Bearer or cookie) |

Sessions are stored in Postgres (`sessions.refresh_token_hash`) and optionally cached in Redis.

## Resumes

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/resumes` | Multipart upload (PDF/DOCX) to MinIO + DB metadata; queues parse |
| GET | `/api/v1/resumes` | List current user's resumes |
| GET | `/api/v1/resumes/{id}` | Get one resume + parsed content when available |
| POST | `/api/v1/resumes/{id}/parse` | Run / re-run parsing into canonical Resume JSON |

Files are stored in MinIO under `users/{user_id}/resumes/{resume_id}/source.{ext}`.
Parsing extracts text (pypdf / python-docx) and structures it with a heuristic parser into
`resume_contents` (`uploaded → parsing → extracted|needs_review|parse_failed`).

## Jobs

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/jobs/discover` | Ingest jobs from Remotive + demo providers (deduped) |
| GET | `/api/v1/jobs` | List/search normalized job postings |
| GET | `/api/v1/jobs/{id}` | Get one job with company |

Discovery upserts `companies`, `job_postings`, `job_sources`, and `job_snapshots`.

## Matches

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/matches/run` | Score jobs against a parsed resume (`heuristic-v1`) |
| GET | `/api/v1/matches` | List saved matches (highest score first) |
| GET | `/api/v1/matches/{id}` | Get one match with explanation + job |

Persists `job_matches` (score, features, explanation) and `skill_gaps` for missing skills.

## LinkedIn (Cursor MCP) + Agents

LinkedIn is **not** used for dashboard SSO or in-app OAuth connect.
Personal LinkedIn access is via Cursor MCP (`mcp-server-linkedin`).

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/agents/job-discovery/run` | Job Discovery agent (Remotive + demo) |
| GET | `/api/v1/agents/mcp/linkedin/tools` | Legacy in-app LinkedIn tool list (unused by UI) |

Dashboard Job Discovery uses Remotive/demo. Use Cursor Agent for `get_my_profile` / `search_jobs`.

## Database

SQLAlchemy models live under `src/careerpilot/domains/*/models.py`.
Alembic migrations live under `alembic/versions/`.

```bash
make migrate                          # upgrade to head
make migrate-create MSG="describe"    # autogenerate revision
make migrate-down                     # downgrade one revision
```
