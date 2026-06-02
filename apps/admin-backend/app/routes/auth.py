"""Admin auth routes — login (admin-only), refresh, me."""

import hashlib
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Body, HTTPException, status
from sqlalchemy import select, update

from starter_shared.config import settings
from starter_shared.security import (
    create_access_token,
    create_refresh_token,
    verify_password,
    verify_token,
)
from starter_shared.types.user import (
    TokenResponse,
    UserLogin,
    UserResponse,
    UserRole,
)

from app.dependencies import CurrentUser, DbSession
from app.models.refresh_token import RefreshToken
from app.models.user import User

router = APIRouter()


def _hash_token(token: str) -> str:
    """SHA-256 hash of a refresh token for DB storage."""
    return hashlib.sha256(token.encode()).hexdigest()


def _create_tokens(user_id: int) -> tuple[TokenResponse, str]:
    """Generate an access + refresh token pair."""
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


@router.post("/login", response_model=TokenResponse)
async def admin_login(body: UserLogin, session: DbSession) -> TokenResponse:
    """Authenticate an admin user. Same users table, requires role=admin."""
    result = await session.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    if user is None or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    tokens, raw_refresh = _create_tokens(user.id)
    await _store_refresh_token(session, user.id, raw_refresh)
    return tokens


@router.post("/refresh", response_model=TokenResponse)
async def refresh(session: DbSession, token: str = Body(...)) -> TokenResponse:
    """Exchange a valid refresh token for a new token pair (rotation)."""
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

    if stored.revoked:
        await session.execute(
            update(RefreshToken).where(RefreshToken.user_id == stored.user_id).values(revoked=True)
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token already used. All sessions terminated.",
        )

    if stored.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expired",
        )

    try:
        uid = int(user_id)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    user_result = await session.execute(select(User).where(User.id == uid))
    user = user_result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    if user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    stored.revoked = True
    tokens, raw_refresh = _create_tokens(user.id)
    await _store_refresh_token(session, user.id, raw_refresh)
    return tokens


@router.get("/me", response_model=UserResponse)
async def me(current_user: CurrentUser) -> UserResponse:
    """Return the authenticated admin user's profile."""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        role=current_user.role,
        created_at=current_user.created_at,
    )
