"""SQLAlchemy User model for admin-backend.

Maps the same 'users' table managed by web-backend's Alembic migrations.
This backend does NOT run migrations — all schema changes go through web-backend.
"""

from datetime import datetime

from sqlalchemy import Enum as SQLEnum
from sqlalchemy import String, func
from sqlalchemy.orm import Mapped, mapped_column

from starter_shared.database import Base
from starter_shared.types.user import UserRole


class User(Base):
    """User account — mirrors web-backend's User model."""

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(64))
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(
        SQLEnum(UserRole, name="user_role"),
        default=UserRole.user,
        server_default="user",
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
