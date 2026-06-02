"""Tests for admin dashboard endpoints — stats."""

import pytest

from app.models.user import User
from starter_shared.security import hash_password

BASE = "/admin/api/v1/dashboard"


@pytest.mark.asyncio
async def test_stats_success(admin_client, admin_user, session):
    """GET /stats returns dashboard statistics with at least the admin user."""
    # Create extra users to make stats more interesting
    for i in range(3):
        user = User(
            email=f"user{i}@example.com",
            name=f"User {i}",
            hashed_password=hash_password("password123"),
            role="user",
        )
        session.add(user)
    editor = User(
        email="editor@example.com",
        name="Editor",
        hashed_password=hash_password("password123"),
        role="editor",
    )
    session.add(editor)
    await session.commit()

    response = await admin_client.get(f"{BASE}/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["total_users"] == 5  # 1 admin + 3 users + 1 editor
    assert data["admin_count"] == 1
    assert data["editor_count"] == 1
    assert data["user_count"] == 3
    assert data["recent_registrations"] >= 5


@pytest.mark.asyncio
async def test_stats_empty(admin_client, admin_user):
    """GET /stats with only the admin user returns correct counts."""
    response = await admin_client.get(f"{BASE}/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["total_users"] == 1
    assert data["admin_count"] == 1
    assert data["editor_count"] == 0
    assert data["user_count"] == 0
    assert data["recent_registrations"] >= 1
