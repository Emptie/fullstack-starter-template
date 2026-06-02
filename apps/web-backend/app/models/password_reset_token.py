"""SQLAlchemy PasswordResetToken model for password reset flow."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from starter_shared.database import Base


class PasswordResetToken(Base):
    """Stores password reset tokens (hashed) for the forgot-password flow.

    Tokens are random strings generated via secrets.token_urlsafe(32).
    Only the SHA-256 hash is stored — the raw token is sent to the user via email.
    Tokens expire after a configurable period (default 1 hour).
    After use, the token is marked as used to prevent replay.
    """

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
