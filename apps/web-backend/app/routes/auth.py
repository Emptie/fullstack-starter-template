"""Auth routes — register, login, refresh, me, forgot-password, reset-password.

Refresh tokens are stored in Redis and rotated on each use.
If a revoked token is replayed, all tokens for that user are revoked
to mitigate token theft.

Password reset tokens are SHA-256 hashed in Redis and expire via TTL.
The email service is pluggable: SMTP if configured, console output otherwise.
"""

import hashlib
import secrets
from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy import select

from starter_shared.config import settings
from starter_shared.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
    verify_token,
)
from starter_shared.token_store import TokenStore, get_token_store
from starter_shared.types.user import (
    ForgotPassword,
    PasswordChange,
    ResetPassword,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
    UserRole,
    UserUpdate,
)

from app.dependencies import CurrentUser, DbSession
from app.models.user import User
from app.services.email import send_password_reset_email

router = APIRouter()
StoreDep = Annotated[TokenStore, Depends(get_token_store)]

# TTL constants (seconds)
_REFRESH_TTL = settings.security.refresh_token_expire_days * 86400
_RESET_TTL = settings.security.password_reset_expire_hours * 3600


def _hash_token(token: str) -> str:
    """SHA-256 hash of a token for Redis key lookup."""
    return hashlib.sha256(token.encode()).hexdigest()


def _create_tokens(user_id: int) -> tuple[TokenResponse, str]:
    """Generate an access + refresh token pair.

    Returns (TokenResponse, raw_refresh_token) so the caller can
    store the hashed refresh token in Redis.
    """
    data = {"sub": str(user_id)}
    access = create_access_token(data)
    refresh = create_refresh_token(data)
    response = TokenResponse(access_token=access, refresh_token=refresh)
    return response, refresh


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(body: UserCreate, session: DbSession, store: StoreDep) -> TokenResponse:
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
        role=UserRole.user,
    )
    session.add(user)
    await session.flush()
    await session.refresh(user)

    tokens, raw_refresh = _create_tokens(user.id)
    await store.store_refresh_token(_hash_token(raw_refresh), user.id, _REFRESH_TTL)
    return tokens


@router.post("/login", response_model=TokenResponse)
async def login(body: UserLogin, session: DbSession, store: StoreDep) -> TokenResponse:
    """Authenticate a user and return JWT tokens."""
    result = await session.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    if user is None or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    tokens, raw_refresh = _create_tokens(user.id)
    await store.store_refresh_token(_hash_token(raw_refresh), user.id, _REFRESH_TTL)
    return tokens


@router.post("/refresh", response_model=TokenResponse)
async def refresh(store: StoreDep, session: DbSession, token: str = Body(...)) -> TokenResponse:
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

    # Look up the token in Redis
    token_hash = _hash_token(token)
    stored_user_id = await store.get_refresh_token(token_hash)

    if stored_user_id is None:
        # Token not found = already revoked/expired → potential replay
        # Try to revoke all tokens for this user as a safety measure
        uid = int(user_id)
        await store.revoke_all_user_refresh_tokens(uid)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token already used. All sessions terminated.",
        )

    # Verify user still exists
    user_result = await session.execute(select(User).where(User.id == stored_user_id))
    user = user_result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    # Rotate: revoke old token, issue new pair
    await store.revoke_refresh_token(token_hash, user.id)
    tokens, raw_refresh = _create_tokens(user.id)
    await store.store_refresh_token(_hash_token(raw_refresh), user.id, _REFRESH_TTL)
    return tokens


@router.get("/me", response_model=UserResponse)
async def me(current_user: CurrentUser) -> UserResponse:
    """Return the authenticated user's profile."""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        role=current_user.role,
        created_at=current_user.created_at,
    )


@router.patch("/me", response_model=UserResponse)
async def update_me(
    body: UserUpdate,
    session: DbSession,
    current_user: CurrentUser,
) -> UserResponse:
    """Update the authenticated user's profile (name)."""
    current_user.name = body.name
    await session.flush()
    await session.refresh(current_user)
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        role=current_user.role,
        created_at=current_user.created_at,
    )


@router.post("/change-password")
async def change_password(
    body: PasswordChange,
    session: DbSession,
    current_user: CurrentUser,
    store: StoreDep,
) -> dict[str, str]:
    """Change the authenticated user's password.

    Verifies the old password before setting the new one.
    """
    if not verify_password(body.old_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    current_user.hashed_password = hash_password(body.new_password)
    await store.revoke_all_user_refresh_tokens(current_user.id)
    await session.flush()
    return {"message": "Password updated successfully"}


@router.post("/forgot-password", status_code=status.HTTP_200_OK)
async def forgot_password(body: ForgotPassword, session: DbSession, store: StoreDep) -> dict:
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

    # Store the hashed token in Redis with TTL
    await store.store_password_reset_token(token_hash, user.id, _RESET_TTL)

    # Send email (SMTP or console fallback)
    await send_password_reset_email(user.email, raw_token)

    return {"message": "If that email is registered, a reset link has been sent."}


@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(body: ResetPassword, session: DbSession, store: StoreDep) -> dict:
    """Verify a password reset token and set a new password.

    The token is looked up by its SHA-256 hash and consumed atomically (GETDEL).
    After successful reset, all refresh tokens are revoked.
    """
    # Atomically consume the reset token
    token_hash = _hash_token(body.token)
    user_id = await store.consume_password_reset_token(token_hash)

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    # Look up the user
    user_result = await session.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found",
        )

    # Update the password
    user.hashed_password = hash_password(body.new_password)

    # Revoke all refresh tokens so compromised sessions are terminated
    await store.revoke_all_user_refresh_tokens(user.id)

    return {"message": "Password has been reset successfully"}
