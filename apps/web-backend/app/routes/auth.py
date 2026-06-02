"""Auth routes — register, login, refresh, me.

Refresh tokens are stored in the database and rotated on each use.
If a revoked token is replayed, all tokens for that user are revoked
to mitigate token theft.
"""

import hashlib
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
    PasswordChange,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
    UserUpdate,
)

from app.dependencies import CurrentUser, DbSession
from app.models.refresh_token import RefreshToken
from app.models.user import User

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
        created_at=current_user.created_at,
    )


@router.post("/change-password")
async def change_password(
    body: PasswordChange,
    session: DbSession,
    current_user: CurrentUser,
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
    await session.flush()
    return {"message": "Password updated successfully"}
