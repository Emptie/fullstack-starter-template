"""Admin-related Pydantic schemas."""

from pydantic import BaseModel


class DashboardStats(BaseModel):
    """Schema for admin dashboard statistics."""

    total_users: int
    admin_count: int
    editor_count: int
    user_count: int
    recent_registrations: int
