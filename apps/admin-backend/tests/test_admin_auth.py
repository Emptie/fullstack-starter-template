"""Tests for admin auth endpoints — login (admin-only), refresh, me."""

import pytest


BASE = "/admin/api/v1/auth"


@pytest.mark.asyncio
async def test_login_success(admin_user):
    """Admin login with correct credentials returns tokens."""
    # admin_user fixture already logged in; verify it has the right shape
    assert "access_token" in admin_user
    assert "refresh_token" in admin_user
    assert admin_user["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    """Login with wrong password returns 401."""
    from starter_shared.security import hash_password

    # Create admin user in DB directly
    async with TestSessionFactory_context(client) as _:
        pass

    # Simpler: insert admin, then try wrong password
    from app.models.user import User
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
    from starter_shared.config import settings
    from starter_shared.database import Base

    test_db_url = settings.db.get_database_url(f"{settings.db.db_name}_test")
    engine = create_async_engine(test_db_url, echo=False)
    factory = async_sessionmaker(engine, expire_on_commit=False)

    async with factory() as s:
        user = User(
            email="admin2@example.com",
            name="Admin Two",
            hashed_password=hash_password("correctpassword"),
            role="admin",
        )
        s.add(user)
        await s.commit()

    response = await client.post(
        f"{BASE}/login",
        json={"email": "admin2@example.com", "password": "wrongpassword"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent_user(client):
    """Login with non-existent email returns 401."""
    response = await client.post(
        f"{BASE}/login",
        json={"email": "ghost@example.com", "password": "whatever"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_non_admin_user(client):
    """Login as a non-admin user returns 403."""
    from starter_shared.security import hash_password

    from app.models.user import User

    async with _test_session() as s:
        user = User(
            email="regular@example.com",
            name="Regular",
            hashed_password=hash_password("regularpassword"),
            role="user",
        )
        s.add(user)
        await s.commit()

    response = await client.post(
        f"{BASE}/login",
        json={"email": "regular@example.com", "password": "regularpassword"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_me_success(admin_client, admin_user):
    """GET /me with valid admin token returns admin profile."""
    response = await admin_client.get(f"{BASE}/me")
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "admin@example.com"
    assert data["name"] == "Admin User"
    assert data["role"] == "admin"
    assert "id" in data


@pytest.mark.asyncio
async def test_me_no_token(client):
    """GET /me without token returns 401."""
    response = await client.get(f"{BASE}/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_invalid_token(client):
    """GET /me with invalid token returns 401."""
    response = await client.get(
        f"{BASE}/me",
        headers={"Authorization": "Bearer invalidtoken"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_success(client, admin_user):
    """Refresh endpoint returns a new token pair (rotation)."""
    response = await client.post(
        f"{BASE}/refresh",
        content=admin_user["refresh_token"],
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    # New tokens should differ from the originals
    assert data["access_token"] != admin_user["access_token"]
    assert data["refresh_token"] != admin_user["refresh_token"]


@pytest.mark.asyncio
async def test_refresh_invalid_token(client):
    """Refresh with an invalid token returns 401."""
    response = await client.post(
        f"{BASE}/refresh",
        content="not-a-valid-token",
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_revoked_token_revoke_all(client, admin_user):
    """Replaying a used refresh token triggers replay detection (401).

    The refresh endpoint should revoke all tokens for the user when
    it detects a previously-used refresh token being replayed.
    """
    # First refresh — succeeds, marks old token as revoked
    response = await client.post(
        f"{BASE}/refresh",
        content=admin_user["refresh_token"],
    )
    assert response.status_code == 200
    new_tokens = response.json()

    # Replay the same (now revoked) refresh token — should trigger replay detection
    response2 = await client.post(
        f"{BASE}/refresh",
        content=admin_user["refresh_token"],
    )
    assert response2.status_code == 401

    # The new refresh token should also be revoked (revoke-all behavior)
    response3 = await client.post(
        f"{BASE}/refresh",
        content=new_tokens["refresh_token"],
    )
    assert response3.status_code == 401


# ── Helpers ───────────────────────────────────────────────────────


async def _test_session():
    """Provide a test database session for manual DB setup."""
    from starter_shared.config import settings
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    test_db_url = settings.db.get_database_url(f"{settings.db.db_name}_test")
    engine = create_async_engine(test_db_url, echo=False)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    return factory()
