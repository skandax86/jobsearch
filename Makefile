.PHONY: help up down logs infra api web install test lint

help: ## Show available commands
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

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
	cd apps/api && . .venv/bin/activate && uvicorn careerpilot.main:app --reload --host 0.0.0.0 --port 8000

web: ## Run Next.js dev server
	cd apps/web && npm run dev

test: ## Run all tests
	cd apps/api && . .venv/bin/activate && pytest
	cd apps/web && npm test

lint: ## Run linters
	cd apps/api && . .venv/bin/activate && ruff check . && ruff format --check .
	cd apps/web && npm run lint
