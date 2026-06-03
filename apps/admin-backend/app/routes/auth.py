"""Admin auth routes — login (admin-only), refresh, me."""

import hashlib
from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy import select

from starter_shared.config import settings
from starter_shared.security import (
    create_access_token,
    create_refresh_token,
    verify_password,
    verify_token,
)
from starter_shared.token_store import TokenStore, get_token_store
from starter_shared.types.user import (
    TokenResponse,
    UserLogin,
    UserResponse,
    UserRole,
)

from app.dependencies import CurrentUser, DbSession
from app.models.user import User

router = APIRouter()
StoreDep = Annotated[TokenStore, Depends(get_token_store)]

_REFRESH_TTL = settings.security.refresh_token_expire_days * 86400


def _hash_token(token: str) -> str:
    """SHA-256 hash of a token for Redis key lookup."""
    return hashlib.sha256(token.encode()).hexdigest()


def _create_tokens(user_id: int) -> tuple[TokenResponse, str]:
    """Generate an access + refresh token pair."""
    data = {"sub": str(user_id)}
    access = create_access_token(data)
    refresh = create_refresh_token(data)
    response = TokenResponse(access_token=access, refresh_token=refresh)
    return response, refresh


@router.post("/login", response_model=TokenResponse)
async def admin_login(body: UserLogin, session: DbSession, store: StoreDep) -> TokenResponse:
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
    await store.store_refresh_token(_hash_token(raw_refresh), user.id, _REFRESH_TTL)
    return tokens


@router.post("/refresh", response_model=TokenResponse)
async def refresh(store: StoreDep, session: DbSession, token: str = Body(...)) -> TokenResponse:
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
    stored_user_id = await store.get_refresh_token(token_hash)

    if stored_user_id is None:
        uid = int(user_id)
        await store.revoke_all_user_refresh_tokens(uid)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token already used. All sessions terminated.",
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

    await store.revoke_refresh_token(token_hash, user.id)
    tokens, raw_refresh = _create_tokens(user.id)
    await store.store_refresh_token(_hash_token(raw_refresh), user.id, _REFRESH_TTL)
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
