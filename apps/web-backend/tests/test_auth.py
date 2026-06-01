"""Tests for auth endpoints — register, login, refresh, me."""

import pytest


@pytest.mark.asyncio
async def test_register_success(client):
    """Register a new user returns 201 with tokens."""
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "new@example.com", "password": "newpassword", "name": "New User"},
    )
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_register_duplicate_email(client, test_user):
    """Registering with an existing email returns 409."""
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "test@example.com", "password": "anotherpassword", "name": "Dup"},
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_register_short_password(client):
    """Registering with a short password returns 422."""
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "short@example.com", "password": "short", "name": "Short"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_success(client, test_user):
    """Login with correct credentials returns tokens."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "testpassword"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_login_wrong_password(client, test_user):
    """Login with wrong password returns 401."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "wrongpassword"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent_user(client):
    """Login with non-existent email returns 401."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@example.com", "password": "whatever"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_success(client, test_user):
    """GET /me with valid token returns user profile."""
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {test_user['access_token']}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["name"] == "Test User"
    assert "id" in data


@pytest.mark.asyncio
async def test_me_no_token(client):
    """GET /me without token returns 401."""
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_invalid_token(client):
    """GET /me with invalid token returns 401."""
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalidtoken"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token(client, test_user):
    """Refresh endpoint returns new token pair."""
    response = await client.post(
        "/api/v1/auth/refresh",
        json=test_user["refresh_token"],
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_refresh_with_access_token(client, test_user):
    """Refresh with an access token (not refresh) returns 401."""
    response = await client.post(
        "/api/v1/auth/refresh",
        json=test_user["access_token"],
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token_rotation(client, test_user):
    """After refresh, the old refresh token is revoked."""
    # First refresh — succeeds
    response = await client.post(
        "/api/v1/auth/refresh",
        json=test_user["refresh_token"],
    )
    assert response.status_code == 200
    new_tokens = response.json()

    # Replay the same refresh token — should be revoked
    response2 = await client.post(
        "/api/v1/auth/refresh",
        json=test_user["refresh_token"],
    )
    assert response2.status_code == 401

    # But the new refresh token works
    response3 = await client.post(
        "/api/v1/auth/refresh",
        json=new_tokens["refresh_token"],
    )
    assert response3.status_code == 200
