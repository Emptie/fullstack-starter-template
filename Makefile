.PHONY: setup dev generate lint typecheck test clean init-db

# ── Setup ──────────────────────────────────────────────

setup: ## Install all dependencies
	uv sync
	cd apps/web-backend && uv sync
	cd packages/shared-py && uv sync
	pnpm install
	@echo "✅ Setup complete. Run 'make dev' to start."

# ── Development ────────────────────────────────────────

dev: ## Start all services (postgres + backend + frontend)
	concurrently --kill-others-on-fail \
		--names "docker,web-be,web-fe" \
		--prefix-colors "blue,green,yellow" \
		"docker compose -f infra/docker-compose.yml up" \
		"cd apps/web-backend && uv run uvicorn app.main:app --reload --port 8000" \
		"cd apps/web-frontend && pnpm dev --port 5173"

dev-db: ## Start only PostgreSQL
	docker compose -f infra/docker-compose.yml up -d

init-db: ## Interactive database setup (prompts for name and prefix)
	uv run python scripts/init_db.py

dev-be: ## Start only backend (requires DB running)
	cd apps/web-backend && uv run uvicorn app.main:app --reload --port 8000

dev-fe: ## Start only frontend
	cd apps/web-frontend && pnpm dev --port 5173

# ── Type Bridge ────────────────────────────────────────

generate: ## Generate TypeScript types from Pydantic models
	uv run python scripts/generate_types.py
	@echo "✅ Types generated in packages/shared-ts/src/types/"

# ── Code Quality ───────────────────────────────────────

lint: ## Lint all code (ruff + eslint)
	uv run ruff check packages/shared-py apps/web-backend
	cd apps/web-frontend && pnpm run lint 2>/dev/null || true

typecheck: ## Type check all code
	cd apps/web-frontend && npx vue-tsc --noEmit
	@echo "✅ Type checking complete"

# ── Testing ────────────────────────────────────────────

test: ## Run all tests
	cd apps/web-backend && uv run pytest
	cd apps/web-frontend && pnpm run test 2>/dev/null || true

test-be: ## Run backend tests only
	cd apps/web-backend && uv run pytest

test-fe: ## Run frontend tests only
	cd apps/web-frontend && pnpm run test

# ── Cleanup ────────────────────────────────────────────

clean: ## Remove generated files and caches
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name node_modules -exec rm -rf {} + 2>/dev/null || true
	rm -rf .venv apps/web-backend/.venv packages/shared-py/.venv
	rm -rf apps/web-frontend/dist
	@echo "✅ Cleaned up"

# ── Help ───────────────────────────────────────────────

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'
