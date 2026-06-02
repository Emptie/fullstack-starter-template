.PHONY: setup dev dev-local dev-docker dev-all dev-admin-be dev-admin-fe generate lint typecheck test clean init-db

# ── Setup ──────────────────────────────────────────────

setup: ## Install all dependencies
	uv sync
	cd apps/web-backend && uv sync
	cd apps/admin-backend && uv sync
	cd packages/shared-py && uv sync
	pnpm install
	@echo "✅ Setup complete. Run 'make dev' to start."

# ── Development ────────────────────────────────────────

dev: dev-local ## Default: start all services (local, no Docker)

dev-local: ## Start backend + frontend (local PostgreSQL, no Docker)
	cd apps/web-backend && uv run alembic upgrade head
	npx concurrently --kill-others-on-fail \
		--names "web-be,web-fe" \
		--prefix-colors "green,yellow" \
		"cd apps/web-backend && uv run uvicorn app.main:app --reload --port 8000" \
		"cd apps/web-frontend && pnpm dev --port 5173"

dev-docker: ## Start all services with Docker PostgreSQL
	cd apps/web-backend && uv run alembic upgrade head
	npx concurrently --kill-others-on-fail \
		--names "docker,web-be,web-fe" \
		--prefix-colors "blue,green,yellow" \
		"docker compose -f infra/docker-compose.yml up" \
		"cd apps/web-backend && uv run uvicorn app.main:app --reload --port 8000" \
		"cd apps/web-frontend && pnpm dev --port 5173"

dev-all: ## Start all 4 services (backend + admin + frontend + admin-frontend)
	cd apps/web-backend && uv run alembic upgrade head
	npx concurrently --kill-others-on-fail \
		--names "web-be,admin-be,web-fe,admin-fe" \
		--prefix-colors "green,cyan,yellow,blue" \
		"cd apps/web-backend && uv run uvicorn app.main:app --reload --port 8000" \
		"cd apps/admin-backend && uv run uvicorn app.main:app --reload --port 8001" \
		"cd apps/web-frontend && pnpm dev --port 5173" \
		"cd apps/admin-frontend && pnpm dev --port 5174"

dev-db: ## Start PostgreSQL via Docker (for deployment testing)
	docker compose -f infra/docker-compose.yml up -d

dev-db-local: ## Check local PostgreSQL is running + ensure database exists
	@/opt/homebrew/opt/postgresql@18/bin/pg_isready -h localhost -p 5432 > /dev/null 2>&1 || (echo "❌ PostgreSQL not running. Start with: brew services start postgresql@18" && exit 1)
	@echo "✅ PostgreSQL is running"
	uv run python scripts/init_db.py

init-db: ## Interactive database setup (prompts for name and prefix)
	uv run python scripts/init_db.py

dev-be: ## Start only backend (requires DB running)
	cd apps/web-backend && uv run uvicorn app.main:app --reload --port 8000

dev-fe: ## Start only frontend
	cd apps/web-frontend && pnpm dev --port 5173

dev-admin-be: ## Start only admin backend (requires DB running)
	cd apps/admin-backend && uv run uvicorn app.main:app --reload --port 8001

dev-admin-fe: ## Start only admin frontend
	cd apps/admin-frontend && pnpm dev --port 5174

# ── Type Bridge ────────────────────────────────────────

generate: ## Generate TypeScript types from Pydantic models
	uv run python scripts/generate_types.py
	@echo "✅ Types generated in packages/shared-ts/src/types/"

# ── Code Quality ───────────────────────────────────────

lint: ## Lint all code (ruff + eslint)
	uv run ruff check packages/shared-py apps/web-backend apps/admin-backend
	cd apps/web-frontend && pnpm run lint 2>/dev/null || true
	cd apps/admin-frontend && pnpm run lint 2>/dev/null || true

typecheck: ## Type check all code
	cd apps/web-frontend && npx vue-tsc --noEmit
	cd apps/admin-frontend && npx vue-tsc --noEmit
	@echo "✅ Type checking complete"

# ── Testing ────────────────────────────────────────────

test: ## Run all tests
	cd apps/web-backend && uv run pytest
	cd apps/admin-backend && uv run pytest
	cd apps/web-frontend && pnpm run test 2>/dev/null || true
	cd apps/admin-frontend && pnpm run test 2>/dev/null || true

test-be: ## Run backend tests only
	cd apps/web-backend && uv run pytest
	cd apps/admin-backend && uv run pytest

test-fe: ## Run frontend tests only
	cd apps/web-frontend && pnpm run test
	cd apps/admin-frontend && pnpm run test

# ── Cleanup ────────────────────────────────────────────

clean: ## Remove generated files and caches
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name node_modules -exec rm -rf {} + 2>/dev/null || true
	rm -rf .venv apps/web-backend/.venv apps/admin-backend/.venv packages/shared-py/.venv
	rm -rf apps/web-frontend/dist apps/admin-frontend/dist
	@echo "✅ Cleaned up"

# ── Help ───────────────────────────────────────────────

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'
