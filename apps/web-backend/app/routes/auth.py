"""Auth routes — register, login, refresh, me, forgot-password, reset-password.

Refresh tokens are stored in the database and rotated on each use.
If a revoked token is replayed, all tokens for that user are revoked
to mitigate token theft.

Password reset tokens are SHA-256 hashed in the database and expire after
a configurable period. The email service is pluggable: SMTP if configured,
console output otherwise.
"""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Body, HTTPException, status
from sqlalchemy import select, update

from starter_shared.config import settings
from starter_shared.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
    verify_token,
)
from starter_shared.types.user import (
    ForgotPassword,
    ResetPassword,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
)

from app.dependencies import CurrentUser, DbSession
from app.models.password_reset_token import PasswordResetToken
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.services.email import send_password_reset_email

router = APIRouter()


def _hash_token(token: str) -> str:
    """SHA-256 hash of a refresh token for DB storage."""
    return hashlib.sha256(token.encode()).hexdigest()


def _create_tokens(user_id: int) -> tuple[TokenResponse, str]:
    """Generate an access + refresh token pair.

    Returns (TokenResponse, raw_refresh_token) so the caller can
    store the hashed refresh token in the database.
    """
    data = {"sub": str(user_id)}
    access = create_access_token(data)
    refresh = create_refresh_token(data)
    response = TokenResponse(access_token=access, refresh_token=refresh)
    return response, refresh


async def _store_refresh_token(session: DbSession, user_id: int, raw_token: str) -> None:
    """Store a new refresh token hash in the database."""
    expires_at = datetime.now(timezone.utc) + timedelta(
        days=settings.security.refresh_token_expire_days
    )
    rt = RefreshToken(
        token_hash=_hash_token(raw_token),
        user_id=user_id,
        expires_at=expires_at,
    )
    session.add(rt)


async def _revoke_all_user_tokens(session: DbSession, user_id: int) -> None:
    """Revoke all refresh tokens for a user (compromise response)."""
    await session.execute(
        update(RefreshToken).where(RefreshToken.user_id == user_id).values(revoked=True)
    )


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(body: UserCreate, session: DbSession) -> TokenResponse:
    """Register a new user and return JWT tokens."""
    result = await session.execute(select(User).where(User.email == body.email))
    if result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    user = User(
        email=body.email,
        name=body.name,
        hashed_password=hash_password(body.password),
    )
    session.add(user)
    await session.flush()
    await session.refresh(user)

    tokens, raw_refresh = _create_tokens(user.id)
    await _store_refresh_token(session, user.id, raw_refresh)
    return tokens


@router.post("/login", response_model=TokenResponse)
async def login(body: UserLogin, session: DbSession) -> TokenResponse:
    """Authenticate a user and return JWT tokens."""
    result = await session.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    if user is None or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    tokens, raw_refresh = _create_tokens(user.id)
    await _store_refresh_token(session, user.id, raw_refresh)
    return tokens


@router.post("/refresh", response_model=TokenResponse)
async def refresh(session: DbSession, token: str = Body(...)) -> TokenResponse:
    """Exchange a valid refresh token for a new token pair (rotation).

    The old token is revoked. If a revoked token is replayed, all
    tokens for that user are revoked (potential theft detection).
    """
    payload = verify_token(token, token_type="refresh")
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    # Look up the token in DB
    token_hash = _hash_token(token)
    result = await session.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    stored = result.scalar_one_or_none()

    if stored is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unknown refresh token",
        )

    # Replay detection: if already revoked, revoke ALL user tokens
    if stored.revoked:
        await _revoke_all_user_tokens(session, stored.user_id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token already used. All sessions terminated.",
        )

    # Check expiry
    if stored.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expired",
        )

    # Verify user still exists
    user_result = await session.execute(select(User).where(User.id == int(user_id)))
    user = user_result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    # Rotate: revoke old token, issue new pair
    stored.revoked = True
    tokens, raw_refresh = _create_tokens(user.id)
    await _store_refresh_token(session, user.id, raw_refresh)
    return tokens


@router.get("/me", response_model=UserResponse)
async def me(current_user: CurrentUser) -> UserResponse:
    """Return the authenticated user's profile."""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        created_at=current_user.created_at,
    )


@router.post("/forgot-password", status_code=status.HTTP_200_OK)
async def forgot_password(body: ForgotPassword, session: DbSession) -> dict:
    """Generate a password reset token and send it via email.

    Always returns 200 even if the email does not exist, to prevent
    email enumeration attacks.
    """
    # Look up the user — but do not reveal whether they exist
    result = await session.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    if user is None:
        # Silently return success to prevent email enumeration
        return {"message": "If that email is registered, a reset link has been sent."}

    # Generate a random token
    raw_token = secrets.token_urlsafe(32)
    token_hash = _hash_token(raw_token)
    expires_at = datetime.now(timezone.utc) + timedelta(
        hours=settings.security.password_reset_expire_hours
    )

    # Store the hashed token
    reset_token = PasswordResetToken(
        token_hash=token_hash,
        user_id=user.id,
        expires_at=expires_at,
    )
    session.add(reset_token)
    await session.flush()

    # Send email (SMTP or console fallback)
    await send_password_reset_email(user.email, raw_token)

    return {"message": "If that email is registered, a reset link has been sent."}


@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(body: ResetPassword, session: DbSession) -> dict:
    """Verify a password reset token and set a new password.

    The token is looked up by its SHA-256 hash. It must not be expired or used.
    After successful reset, the token is marked as used.
    """
    # Hash the provided token to look it up
    token_hash = _hash_token(body.token)
    result = await session.execute(
        select(PasswordResetToken).where(
            PasswordResetToken.token_hash == token_hash
        )
    )
    reset_token = result.scalar_one_or_none()

    if reset_token is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    # Check if already used
    if reset_token.used:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This reset token has already been used",
        )

    # Check expiry
    if reset_token.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has expired",
        )

    # Look up the user
    user_result = await session.execute(
        select(User).where(User.id == reset_token.user_id)
    )
    user = user_result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found",
        )

    # Update the password
    user.hashed_password = hash_password(body.new_password)

    # Mark token as used
    reset_token.used = True

    return {"message": "Password has been reset successfully"}
