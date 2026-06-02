"""Admin backend FastAPI application.

Admin-only API for the admin frontend. Runs on port 8001.
"""

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from starter_shared.config import settings
from starter_shared.constants import ADMIN_API_V1_PREFIX

from app.routes import auth, dashboard, users


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: startup and shutdown logic."""
    yield
    from starter_shared.database import engine

    await engine.dispose()


app = FastAPI(
    title="Fullstack Starter - Admin API",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS: allow both frontend dev servers
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        f"http://localhost:{settings.web_frontend_port}",
        f"http://localhost:{settings.admin_frontend_port}",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(auth.router, prefix=f"{ADMIN_API_V1_PREFIX}/auth", tags=["auth"])
app.include_router(dashboard.router, prefix=f"{ADMIN_API_V1_PREFIX}/dashboard", tags=["dashboard"])
app.include_router(users.router, prefix=f"{ADMIN_API_V1_PREFIX}/users", tags=["users"])
