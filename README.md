# Fullstack Starter Template

Vue 3 + FastAPI monorepo starter template with shared types and vibe-coding friendly structure.

## Quick Start

```bash
# Install dependencies
make setup

# Start development environment
make dev
```

## Architecture

See [CLAUDE.md](CLAUDE.md) for full architecture documentation.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Web Frontend | Vue 3 + Vite + shadcn-vue + Tailwind CSS |
| Admin Frontend | Vue 3 + Vite + shadcn-vue + Tailwind CSS |
| Web Backend | FastAPI + SQLAlchemy 2.0 + Alembic |
| Admin Backend | FastAPI + SQLAlchemy 2.0 + Alembic |
| Shared Types | Pydantic → TypeScript (type bridge) |
| Database | PostgreSQL |
| Auth | JWT + Refresh Token |
| Testing | Vitest + pytest |

## Commands

| Command | Description |
|---------|-------------|
| `make setup` | Install all dependencies |
| `make dev` | Start all services with hot-reload |
| `make generate` | Run type bridge (Pydantic → TypeScript) |
| `make lint` | Lint all code |
| `make typecheck` | Type check all code |
| `make test` | Run all tests |
