"""Test fixtures for web-backend.

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

# Import models so they register with Base.metadata before table creation
from app.models.user import User  # noqa: F401

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
async def test_user(client: AsyncClient) -> dict:
    """Create a test user and return their data + tokens."""
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "test@example.com", "password": "testpassword", "name": "Test User"},
    )
    assert response.status_code == 201
    return response.json()
