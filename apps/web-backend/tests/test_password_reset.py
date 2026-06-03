"""Tests for password reset endpoints — forgot-password, reset-password."""

import hashlib
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import select

from app.models.password_reset_token import PasswordResetToken


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
async def test_forgot_password_creates_hashed_token(client, test_user, session):
    """The stored token is a SHA-256 hash, not the raw token."""
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

    # The stored hash should be the SHA-256 of the raw token
    expected_hash = hashlib.sha256(captured_token.encode()).hexdigest()
    result = await session.execute(
        select(PasswordResetToken).where(
            PasswordResetToken.token_hash == expected_hash
        )
    )
    stored = result.scalar_one_or_none()
    assert stored is not None
    assert stored.used is False


@pytest.mark.asyncio
async def test_reset_password_success(client, test_user, session):
    """Reset password with a valid token updates the password."""
    import secrets

    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

    reset_entry = PasswordResetToken(
        token_hash=token_hash,
        user_id=1,  # test_user id
        expires_at=expires_at,
    )
    session.add(reset_entry)
    await session.commit()

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
async def test_reset_password_expired_token(client, test_user, session):
    """Reset password with an expired token returns 400."""
    import secrets

    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    # Expired 1 hour ago
    expires_at = datetime.now(timezone.utc) - timedelta(hours=1)

    reset_entry = PasswordResetToken(
        token_hash=token_hash,
        user_id=1,
        expires_at=expires_at,
    )
    session.add(reset_entry)
    await session.commit()

    response = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": raw_token, "new_password": "newpassword123"},
    )
    assert response.status_code == 400
    assert "expired" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_reset_password_already_used_token(client, test_user, session):
    """Reset password with an already used token returns 400."""
    import secrets

    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

    reset_entry = PasswordResetToken(
        token_hash=token_hash,
        user_id=1,
        expires_at=expires_at,
        used=True,
    )
    session.add(reset_entry)
    await session.commit()

    response = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": raw_token, "new_password": "newpassword123"},
    )
    assert response.status_code == 400
    assert "already been used" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_reset_password_short_password(client):
    """Reset password with too short password returns 422."""
    response = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": "sometoken", "new_password": "short"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_reset_password_marks_token_used(client, test_user, session):
    """After successful reset, the token is marked as used and cannot be reused."""
    import secrets

    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

    reset_entry = PasswordResetToken(
        token_hash=token_hash,
        user_id=1,
        expires_at=expires_at,
    )
    session.add(reset_entry)
    await session.commit()

    # First reset — should succeed
    response = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": raw_token, "new_password": "newpassword123"},
    )
    assert response.status_code == 200

    # Second reset with same token — should fail
    response2 = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": raw_token, "new_password": "anotherpassword"},
    )
    assert response2.status_code == 400
    assert "already been used" in response2.json()["detail"].lower()
