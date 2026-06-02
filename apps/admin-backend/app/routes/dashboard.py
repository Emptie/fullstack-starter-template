"""Admin dashboard routes."""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter
from sqlalchemy import func, select

from starter_shared.types.admin import DashboardStats
from starter_shared.types.user import UserRole

from app.dependencies import CurrentUser, DbSession
from app.models.user import User

router = APIRouter()


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(session: DbSession, current_user: CurrentUser) -> DashboardStats:
    """Return basic dashboard statistics."""
    total_users = (await session.scalar(select(func.count(User.id)))) or 0
    admin_count = (
        await session.scalar(select(func.count(User.id)).where(User.role == UserRole.admin))
    ) or 0
    editor_count = (
        await session.scalar(select(func.count(User.id)).where(User.role == UserRole.editor))
    ) or 0
    thirty_days_ago = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=30)
    recent_registrations = (
        await session.scalar(select(func.count(User.id)).where(User.created_at >= thirty_days_ago))
    ) or 0

    return DashboardStats(
        total_users=total_users,
        admin_count=admin_count,
        editor_count=editor_count,
        user_count=total_users - admin_count - editor_count,
        recent_registrations=recent_registrations,
    )
