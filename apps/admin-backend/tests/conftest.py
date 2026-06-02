"""Test fixtures for admin-backend.

Uses local PostgreSQL with a dedicated test database ({db_name}_test).
Tables are created/dropped per test for guaranteed clean state.
"""

from collections.abc import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from starter_shared.config import settings
from starter_shared.database import Base, get_session
from starter_shared.security import hash_password

# Import models so they register with Base.metadata before table creation
from app.models.user import User  # noqa: F401
from app.models.refresh_token import RefreshToken  # noqa: F401

# Build test database URL: same server, database name with _test suffix
test_db_url = settings.db.get_database_url(f"{settings.db.db_name}_test")

test_engine = create_async_engine(test_db_url, echo=False, poolclass=NullPool)
TestSessionFactory = async_sessionmaker(test_engine, expire_on_commit=False)


@pytest_asyncio.fixture(autouse=True)
async def setup_database():
    """Create all tables before each test, drop them after."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a test database session."""
    async with TestSessionFactory() as s:
        yield s


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Provide an async HTTP test client with DB dependency overridden."""
    from app.main import app

    async def override_session():
        async with TestSessionFactory() as s:
            yield s
            await s.commit()

    app.dependency_overrides[get_session] = override_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def admin_user(client: AsyncClient) -> dict:
    """Create an admin user directly in the DB, then log in to get tokens."""
    from sqlalchemy import select

    async with TestSessionFactory() as s:
        user = User(
            email="admin@example.com",
            name="Admin User",
            hashed_password=hash_password("adminpassword"),
            role="admin",
        )
        s.add(user)
        await s.commit()
        await s.refresh(user)
        admin_id = user.id

    # Log in via the admin login endpoint
    response = await client.post(
        "/admin/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "adminpassword"},
    )
    assert response.status_code == 200
    tokens = response.json()
    return {**tokens, "id": admin_id, "email": "admin@example.com"}


@pytest_asyncio.fixture
async def admin_client(client: AsyncClient, admin_user: dict) -> AsyncClient:
    """Provide a client authenticated as admin."""
    client.headers["Authorization"] = f"Bearer {admin_user['access_token']}"
    return client


@pytest_asyncio.fixture
async def regular_user(client: AsyncClient) -> dict:
    """Create a regular (non-admin) user and return their data + tokens.

    Uses the web-backend register endpoint pattern via direct DB insertion,
    then creates tokens manually since admin login blocks non-admin users.
    """
    from starter_shared.security import create_access_token, create_refresh_token

    async with TestSessionFactory() as s:
        user = User(
            email="user@example.com",
            name="Regular User",
            hashed_password=hash_password("userpassword"),
            role="user",
        )
        s.add(user)
        await s.commit()
        await s.refresh(user)
        uid = user.id

    access = create_access_token({"sub": str(uid)})
    refresh = create_refresh_token({"sub": str(uid)})
    return {
        "access_token": access,
        "refresh_token": refresh,
        "id": uid,
        "email": "user@example.com",
    }


@pytest_asyncio.fixture
async def regular_client(client: AsyncClient, regular_user: dict) -> AsyncClient:
    """Provide a client authenticated as a regular (non-admin) user."""
    client.headers["Authorization"] = f"Bearer {regular_user['access_token']}"
    return client
