# CLAUDE.md — Fullstack Starter Template

## Architecture Overview

```
fullstack-starter-template/
├── apps/
│   ├── web-frontend/      Vue 3 + Vite + shadcn-vue + Tailwind   (port 5173)
│   ├── web-backend/       FastAPI + SQLAlchemy 2.0               (port 8000)
│   ├── admin-frontend/    Vue 3 + Vite + shadcn-vue + Tailwind   (port 5174)
│   └── admin-backend/     FastAPI + SQLAlchemy 2.0               (port 8001)
├── packages/
│   ├── shared-py/         Python shared: types, db, config, security, utils
│   └── shared-ts/         TypeScript shared: generated types, constants, utils
├── infra/
│   ├── docker-compose.yml PostgreSQL 16                          (port 5432)
│   └── .env.example
├── scripts/
│   └── generate_types.py  Pydantic → TypeScript type bridge
├── Makefile                dev/generate/lint/typecheck/test targets
└── pnpm-workspace.yaml
```

## App Boundaries

| App | Port | Entry | Role |
|-----|------|-------|------|
| web-backend | 8000 | `app.main:app` | Public-facing REST API |
| web-frontend | 5173 | `src/main.ts` | Public-facing SPA |
| admin-backend | 8001 | `app.main:app` | Admin-only REST API (role-gated) |
| admin-frontend | 5174 | `src/main.ts` | Admin panel SPA |
| PostgreSQL | 5432 | docker-compose | Database |

## Key Architecture Decisions

- **Shared database:** All backends use the same PostgreSQL database via `starter_shared.database`
- **Single Alembic owner:** Only `web-backend` manages migrations. `admin-backend` maps the same tables with its own model classes but has no Alembic setup.
- **Role-based access:** `UserRole` enum (admin/editor/user) is stored on the `users` table. Admin-backend checks `role=admin` on every request via `get_current_admin_user` dependency.
- **Separate auth sessions:** Admin-frontend uses `admin_access_token`/`admin_refresh_token` localStorage keys to avoid collision with web-frontend.

## How to Add a New Feature

1. **Define Pydantic model** in `packages/shared-py/src/starter_shared/types/`
2. **Run `make generate`** to generate TypeScript types in `packages/shared-ts/src/types/`
3. **Add SQLAlchemy model** in `apps/web-backend/app/models/`
4. **Create Alembic migration** with `cd apps/web-backend && uv run alembic revision --autogenerate -m "description"`
5. **If admin needs the model**, mirror it in `apps/admin-backend/app/models/` (same table name, same columns)
6. **Add API route** in `apps/web-backend/app/routes/` and/or `apps/admin-backend/app/routes/`
7. **Add API client call** in `apps/web-frontend/src/api/` and/or `apps/admin-frontend/src/api/`
8. **Create Vue component** in `apps/.../src/views/` or `components/`

## Naming Conventions

- Python package: `starter_shared` (import as `from starter_shared.xxx import Yyy`)
- TypeScript package: `@starter/shared` (import as `import { Yyy } from "@starter/shared"`)
- Type bridge whitelist: edit `EXPORT_MODELS` in `scripts/generate_types.py`
- Backend routes: `apps/web-backend/app/routes/<domain>.py`
- Admin routes: `apps/admin-backend/app/routes/<domain>.py`
- Frontend views: `apps/web-frontend/src/views/<Page>.vue`
- Admin views: `apps/admin-frontend/src/views/<Page>.vue`

## Type Bridge

Pydantic models → JSON Schema → TypeScript types.

1. Add model to `starter_shared/types/` and export from `__init__.py`
2. Add model class name to `EXPORT_MODELS` in `scripts/generate_types.py`
3. Run `make generate`
4. Generated TS files appear in `packages/shared-ts/src/types/`

Note: Enums (like `UserRole`) are NOT in EXPORT_MODELS — they appear as type aliases in generated types. Manual re-exports can be added to `packages/shared-ts/src/types/index.ts`.

Run `make generate` whenever you change Pydantic models in shared-py.

## Development Commands

| Command | What it does |
|---------|-------------|
| `make setup` | Install all dependencies |
| `make dev` | Start postgres + web-backend + web-frontend |
| `make dev-all` | Start all 4 services (web + admin) |
| `make dev-admin-be` | Start only admin backend |
| `make dev-admin-fe` | Start only admin frontend |
| `make dev-db` | Start only PostgreSQL (Docker) |
| `make dev-be` | Start only web backend |
| `make dev-fe` | Start only web frontend |
| `make generate` | Run type bridge (Pydantic → TS) |
| `make lint` | Lint Python + TypeScript |
| `make typecheck` | Type check all code |
| `make test` | Run all tests |

## Individual App Startup

```bash
# Backend only (needs DB running)
make dev-db
make dev-be

# Frontend only
make dev-fe

# Admin backend only
make dev-admin-be

# Admin frontend only
make dev-admin-fe

# Everything
make dev-all
```

## Tech Stack

- **Frontend:** Vue 3.5 + Vite 8 + shadcn-vue + Tailwind CSS 4 + TypeScript 6
- **Backend:** FastAPI + SQLAlchemy 2.0 (async) + Alembic + Pydantic 2
- **Database:** PostgreSQL 16
- **Auth:** JWT + Refresh Token + UserRole enum
- **Testing:** Vitest + pytest
- **Monorepo:** pnpm workspaces + uv workspaces
