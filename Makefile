.PHONY: help up down logs infra api web install test lint migrate migrate-create migrate-down naukri-mcp-setup check-contracts resume-mcp

help: ## Show available commands
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

up: ## Start infrastructure (Postgres, Redis, MinIO)
	docker compose up -d

down: ## Stop infrastructure
	docker compose down

logs: ## Tail infrastructure logs
	docker compose logs -f

infra: up ## Alias for up

install: ## Install all dependencies
	cd apps/api && python3 -m venv .venv && . .venv/bin/activate && pip install -e ".[dev]"
	cd apps/web && npm install

api: ## Run FastAPI dev server
	cd apps/api && . .venv/bin/activate && PYTHONPATH=src uvicorn careerpilot.main:app --reload --host 0.0.0.0 --port 8000

web: ## Run Next.js dev server
	cd apps/web && npm run dev

migrate: ## Apply database migrations
	cd apps/api && . .venv/bin/activate && PYTHONPATH=src alembic upgrade head

migrate-create: ## Create a new migration (usage: make migrate-create MSG="add foo")
	cd apps/api && . .venv/bin/activate && PYTHONPATH=src alembic revision --autogenerate -m "$(MSG)"

migrate-down: ## Roll back one migration
	cd apps/api && . .venv/bin/activate && PYTHONPATH=src alembic downgrade -1

naukri-mcp-setup: ## Clone + install Naukri MCP (Cursor + in-app discovery)
	@mkdir -p tools
	@if [ ! -d tools/naukri-mcp/.git ]; then \
		git clone --depth 1 https://github.com/sanjeev-txt/Naukri-MCP.git tools/naukri-mcp; \
	fi
	cd tools/naukri-mcp && uv venv .venv && . .venv/bin/activate && uv pip install -r requirements.txt && playwright install chromium
	@test -f .env.naukri || cp .env.naukri.example .env.naukri
	cd apps/api && . .venv/bin/activate && pip install -e '.[naukri]' && playwright install chromium
	@echo "Fill credentials in .env.naukri. Dashboard: enable Naukri checkbox. Cursor: enable naukri-mcp in Settings → MCP."

check-contracts: ## Validate ACP/MCP/agent contracts vs runtime
	cd apps/api && . .venv/bin/activate && PYTHONPATH=src python ../../tools/check-contracts.py

resume-mcp: ## Smoke-list resume MCP tools
	cd apps/api && . .venv/bin/activate && PYTHONPATH=src python -c "from careerpilot.mcp.resume.server import resume_mcp; print(resume_mcp.list_tools())"

test: ## Run all tests
	cd apps/api && . .venv/bin/activate && PYTHONPATH=src pytest
	cd apps/web && npm test

lint: ## Run linters
	cd apps/api && . .venv/bin/activate && ruff check . && ruff format --check .
	cd apps/web && npm run lint
