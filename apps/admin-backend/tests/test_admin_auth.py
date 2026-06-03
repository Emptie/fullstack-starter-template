"""Tests for admin auth endpoints — login (admin-only), refresh, me."""

import pytest

from app.models.user import User
from starter_shared.security import hash_password

BASE = "/admin/api/v1/auth"


@pytest.mark.asyncio
async def test_login_success(admin_user):
    """Admin login with correct credentials returns tokens."""
    assert "access_token" in admin_user
    assert "refresh_token" in admin_user
    assert admin_user["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client, session):
    """Login with wrong password returns 401."""
    user = User(
        email="admin2@example.com",
        name="Admin Two",
        hashed_password=hash_password("correctpassword"),
        role="admin",
    )
    session.add(user)
    await session.commit()

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
async def test_login_non_admin_user(client, session):
    """Login as a non-admin user returns 403."""
    user = User(
        email="regular@example.com",
        name="Regular",
        hashed_password=hash_password("regularpassword"),
        role="user",
    )
    session.add(user)
    await session.commit()

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
    """Replaying a used refresh token returns 401 (replay detection).

    The old refresh token is revoked after first use. Replaying it
    triggers the replay detection path which returns 401.
    """
    # First refresh — succeeds, marks old token as revoked
    response = await client.post(
        f"{BASE}/refresh",
        content=admin_user["refresh_token"],
    )
    assert response.status_code == 200

    # Replay the same (now revoked) refresh token — should be rejected
    response2 = await client.post(
        f"{BASE}/refresh",
        content=admin_user["refresh_token"],
    )
    assert response2.status_code == 401
