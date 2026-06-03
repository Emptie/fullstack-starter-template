"""Tests for password reset endpoints — forgot-password, reset-password."""

import asyncio
import hashlib
import secrets
from unittest.mock import AsyncMock, patch

import pytest
from redis.asyncio import Redis

from starter_shared.config import settings


def _get_test_redis() -> Redis:
    """Get a Redis client connected to the test DB."""
    url = settings.redis.redis_url.rstrip("/").rsplit("/", 1)[0] + "/1"
    return Redis.from_url(url, decode_responses=True)


async def _get_user_id(client, test_user: dict) -> int:
    """Get user ID from /me endpoint."""
    me_response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {test_user['access_token']}"},
    )
    return me_response.json()["id"]


@pytest.mark.asyncio
async def test_forgot_password_existing_user(client, test_user):
    """Forgot password for an existing user returns 200 and creates a token."""
    with patch("app.routes.auth.send_password_reset_email", new_callable=AsyncMock):
        response = await client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "test@example.com"},
        )
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "reset link" in data["message"].lower()


@pytest.mark.asyncio
async def test_forgot_password_nonexistent_user(client):
    """Forgot password for a non-existent user still returns 200 (no enumeration)."""
    response = await client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "nobody@example.com"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "message" in data


@pytest.mark.asyncio
async def test_forgot_password_invalid_email(client):
    """Forgot password with invalid email format returns 422."""
    response = await client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "not-an-email"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_forgot_password_creates_hashed_token(client, test_user):
    """The stored token is a SHA-256 hash in Redis, not the raw token."""
    captured_token = None

    async def mock_send(email, token):
        nonlocal captured_token
        captured_token = token

    with patch("app.routes.auth.send_password_reset_email", side_effect=mock_send):
        response = await client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "test@example.com"},
        )
    assert response.status_code == 200
    assert captured_token is not None

    # The stored key should be prt:<sha256(raw_token)>
    expected_hash = hashlib.sha256(captured_token.encode()).hexdigest()
    redis = _get_test_redis()
    try:
        val = await redis.get(f"prt:{expected_hash}")
        assert val is not None  # token exists in Redis
    finally:
        await redis.aclose()


@pytest.mark.asyncio
async def test_reset_password_success(client, test_user):
    """Reset password with a valid token updates the password."""
    user_id = await _get_user_id(client, test_user)
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

    redis = _get_test_redis()
    try:
        await redis.set(f"prt:{token_hash}", str(user_id), ex=3600)
    finally:
        await redis.aclose()

    response = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": raw_token, "new_password": "newpassword123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "success" in data["message"].lower()

    # Verify password was actually changed by logging in
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "newpassword123"},
    )
    assert login_response.status_code == 200


@pytest.mark.asyncio
async def test_reset_password_invalid_token(client):
    """Reset password with an invalid token returns 400."""
    response = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": "invalidtoken123", "new_password": "newpassword123"},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_reset_password_expired_token(client, test_user):
    """Reset password with an expired token returns 400."""
    user_id = await _get_user_id(client, test_user)
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

    redis = _get_test_redis()
    try:
        await redis.set(f"prt:{token_hash}", str(user_id), ex=1)
    finally:
        await redis.aclose()

    await asyncio.sleep(1.1)

    response = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": raw_token, "new_password": "newpassword123"},
    )
    assert response.status_code == 400
    assert "invalid or expired" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_reset_password_already_used_token(client, test_user):
    """Reset password with an already used token returns 400."""
    user_id = await _get_user_id(client, test_user)
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

    redis = _get_test_redis()
    try:
        await redis.set(f"prt:{token_hash}", str(user_id), ex=3600)
        await redis.getdel(f"prt:{token_hash}")  # consume it
    finally:
        await redis.aclose()

    response = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": raw_token, "new_password": "newpassword123"},
    )
    assert response.status_code == 400
    assert "invalid or expired" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_reset_password_short_password(client):
    """Reset password with too short password returns 422."""
    response = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": "sometoken", "new_password": "short"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_reset_password_marks_token_used(client, test_user):
    """After successful reset, the token is consumed and cannot be reused."""
    user_id = await _get_user_id(client, test_user)
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

    redis = _get_test_redis()
    try:
        await redis.set(f"prt:{token_hash}", str(user_id), ex=3600)
    finally:
        await redis.aclose()

    # First reset — should succeed
    response = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": raw_token, "new_password": "newpassword123"},
    )
    assert response.status_code == 200

    # Second reset with same token — should fail (GETDEL consumed it)
    response2 = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": raw_token, "new_password": "anotherpassword"},
    )
    assert response2.status_code == 400
    assert "invalid or expired" in response2.json()["detail"].lower()
