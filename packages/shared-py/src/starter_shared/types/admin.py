"""Admin-related Pydantic schemas."""

from __future__ import annotations

from pydantic import BaseModel

from starter_shared.types.user import UserResponse


class DashboardStats(BaseModel):
    """Schema for admin dashboard statistics."""

    total_users: int
    admin_count: int
    editor_count: int
    user_count: int
    recent_registrations: int


class PaginatedUserResponse(BaseModel):
    """Schema for paginated user list responses."""

    items: list[UserResponse]
    total: int
    skip: int
    limit: int
