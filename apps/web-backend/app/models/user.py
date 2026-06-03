"""SQLAlchemy User model."""

from datetime import datetime

from sqlalchemy import Enum as SQLEnum
from sqlalchemy import String, func
from sqlalchemy.orm import Mapped, mapped_column

from starter_shared.database import Base
from starter_shared.types.user import UserRole


class User(Base):
    """User account stored in the database.

    Password is stored as a bcrypt hash via passlib.
    """

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(64))
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole, name="user_role", create_constraint=True),
        default=UserRole.user,
        server_default="user",
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
