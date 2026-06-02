"""Tests for admin user management endpoints — list, get, create, update, delete."""

import pytest
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from sqlalchemy import select

from app.models.refresh_token import RefreshToken
from app.models.user import User
from starter_shared.security import (
    create_refresh_token,
    hash_password,
    verify_password,
)

BASE = "/admin/api/v1/users"


@pytest.mark.asyncio
async def test_list_users_default(admin_client, session):
    """GET / returns paginated user list containing the admin."""
    response = await admin_client.get(f"{BASE}/")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert data["total"] >= 1
    assert data["skip"] == 0
    assert data["limit"] == 50


@pytest.mark.asyncio
async def test_list_users_with_search(admin_client, session):
    """GET /?search= filters users by email or name."""
    # Create an extra user to search for
    user = User(
        email="searchable@example.com",
        name="Searchable User",
        hashed_password=hash_password("password123"),
        role="user",
    )
    session.add(user)
    await session.commit()

    response = await admin_client.get(f"{BASE}/", params={"search": "searchable"})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert any(u["email"] == "searchable@example.com" for u in data["items"])


@pytest.mark.asyncio
async def test_list_users_with_role_filter(admin_client, session):
    """GET /?role=admin returns only admin users."""
    response = await admin_client.get(f"{BASE}/", params={"role": "admin"})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert all(u["role"] == "admin" for u in data["items"])


@pytest.mark.asyncio
async def test_list_users_pagination(admin_client, session):
    """GET /?skip=0&limit=1 returns at most 1 user."""
    response = await admin_client.get(f"{BASE}/", params={"skip": 0, "limit": 1})
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) <= 1
    assert data["limit"] == 1
    assert data["skip"] == 0


@pytest.mark.asyncio
async def test_get_user_found(admin_client, admin_user, session):
    """GET /{user_id} returns the requested user."""
    response = await admin_client.get(f"{BASE}/{admin_user['id']}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == admin_user["id"]
    assert data["email"] == "admin@example.com"


@pytest.mark.asyncio
async def test_get_user_not_found(admin_client):
    """GET /{user_id} with non-existent ID returns 404."""
    response = await admin_client.get(f"{BASE}/999999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_user_success(admin_client):
    """POST / creates a new user and returns 201."""
    response = await admin_client.post(
        f"{BASE}/",
        json={
            "email": "newuser@example.com",
            "password": "newpassword1",
            "name": "New User",
            "role": "user",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert data["name"] == "New User"
    assert data["role"] == "user"
    assert "id" in data
    assert "hashed_password" not in data


@pytest.mark.asyncio
async def test_create_user_duplicate_email(admin_client, admin_user):
    """POST / with existing email returns 409."""
    response = await admin_client.post(
        f"{BASE}/",
        json={
            "email": "admin@example.com",
            "password": "password123",
            "name": "Duplicate",
            "role": "user",
        },
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_update_user_success(admin_client, session):
    """PATCH /{user_id} updates user fields."""
    # Create a user to update
    user = User(
        email="updateme@example.com",
        name="Before Update",
        hashed_password=hash_password("password123"),
        role="user",
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)

    response = await admin_client.patch(
        f"{BASE}/{user.id}",
        json={
            "name": "After Update",
            "email": "updated@example.com",
            "role": "editor",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "After Update"
    assert data["email"] == "updated@example.com"
    assert data["role"] == "editor"


@pytest.mark.asyncio
async def test_update_user_not_found(admin_client):
    """PATCH /{user_id} with non-existent ID returns 404."""
    response = await admin_client.patch(
        f"{BASE}/999999",
        json={"name": "Ghost", "email": "ghost@example.com", "role": "user"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_self_role_change(admin_client, admin_user):
    """PATCH /{self_id} trying to change own role returns 400."""
    response = await admin_client.patch(
        f"{BASE}/{admin_user['id']}",
        json={
            "name": "Admin User",
            "email": "admin@example.com",
            "role": "user",
        },
    )
    assert response.status_code == 400
    assert "own role" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_update_last_admin_demotion(admin_client, admin_user, session):
    """PATCH demoting a second admin (leaving one) succeeds, then self-demotion is blocked.

    The route prevents demoting the last admin. When there are 2+ admins,
    demotion succeeds. But the logged-in admin cannot demote themselves,
    which effectively prevents reducing admin count to zero.
    """
    # Create a second admin
    admin2 = User(
        email="admin2@example.com",
        name="Admin Two",
        hashed_password=hash_password("admin2password"),
        role="admin",
    )
    session.add(admin2)
    await session.commit()
    await session.refresh(admin2)

    # Demote admin #2 (succeeds because admin #1 still exists)
    response = await admin_client.patch(
        f"{BASE}/{admin2.id}",
        json={
            "name": admin2.name,
            "email": admin2.email,
            "role": "user",
        },
    )
    assert response.status_code == 200
    assert response.json()["role"] == "user"

    # Now only one admin remains (the logged-in admin).
    # Trying to demote self is blocked by the self-role-change guard.
    response2 = await admin_client.patch(
        f"{BASE}/{admin_user['id']}",
        json={
            "name": "Admin User",
            "email": "admin@example.com",
            "role": "user",
        },
    )
    assert response2.status_code == 400
    assert "own role" in response2.json()["detail"].lower()


@pytest.mark.asyncio
async def test_delete_user_success(admin_client, session):
    """DELETE /{user_id} deletes the user and returns 204."""
    user = User(
        email="deleteme@example.com",
        name="Delete Me",
        hashed_password=hash_password("password123"),
        role="user",
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)

    response = await admin_client.delete(f"{BASE}/{user.id}")
    assert response.status_code == 204

    # Verify user is gone
    result = await session.execute(select(User).where(User.id == user.id))
    assert result.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_delete_self(admin_client, admin_user):
    """DELETE /{self_id} returns 400."""
    response = await admin_client.delete(f"{BASE}/{admin_user['id']}")
    assert response.status_code == 400
    assert "yourself" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_delete_user_not_found(admin_client):
    """DELETE /{user_id} with non-existent ID returns 404."""
    response = await admin_client.delete(f"{BASE}/999999")
    assert response.status_code == 404


# --- Reset password ---


@pytest.mark.asyncio
async def test_reset_password_success(admin_client, session):
    """PATCH /{user_id}/password resets the password and returns 204."""
    user = User(
        email="resetme@example.com",
        name="Reset Me",
        hashed_password=hash_password("oldpassword1"),
        role="user",
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)

    response = await admin_client.patch(
        f"{BASE}/{user.id}/password",
        json={"new_password": "newpassword1"},
    )
    assert response.status_code == 204

    # Verify the password actually changed
    await session.refresh(user)
    assert verify_password("newpassword1", user.hashed_password)


@pytest.mark.asyncio
async def test_reset_password_user_not_found(admin_client):
    """PATCH /{user_id}/password with non-existent ID returns 404."""
    response = await admin_client.patch(
        f"{BASE}/999999/password",
        json={"new_password": "newpassword1"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_reset_password_validation_too_short(admin_client, session):
    """PATCH /{user_id}/password with short password returns 422."""
    user = User(
        email="short@example.com",
        name="Short Password",
        hashed_password=hash_password("oldpassword1"),
        role="user",
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)

    response = await admin_client.patch(
        f"{BASE}/{user.id}/password",
        json={"new_password": "short"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_reset_password_revokes_refresh_tokens(admin_client, session):
    """PATCH /{user_id}/password deletes all refresh tokens for the user."""
    user = User(
        email="tokenuser@example.com",
        name="Token User",
        hashed_password=hash_password("oldpassword1"),
        role="user",
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)

    # Create a refresh token for this user
    token = create_refresh_token({"sub": str(user.id)})
    token_hash = sha256(token.encode()).hexdigest()

    refresh_token = RefreshToken(
        token_hash=token_hash,
        user_id=user.id,
        expires_at=datetime.now(tz=timezone.utc) + timedelta(days=7),
    )
    session.add(refresh_token)
    await session.commit()

    # Verify the token exists
    result = await session.execute(
        select(RefreshToken).where(RefreshToken.user_id == user.id)
    )
    assert result.scalar_one_or_none() is not None

    # Reset the password
    response = await admin_client.patch(
        f"{BASE}/{user.id}/password",
        json={"new_password": "newpassword1"},
    )
    assert response.status_code == 204

    # Verify the refresh token was deleted
    await session.flush()
    result = await session.execute(
        select(RefreshToken).where(RefreshToken.user_id == user.id)
    )
    assert result.scalar_one_or_none() is None
