"""Auth routes — register, login, refresh, me."""

from fastapi import APIRouter, Body, HTTPException, status
from sqlalchemy import select

from starter_shared.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
    verify_token,
)
from starter_shared.types.user import (
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
)

from app.dependencies import CurrentUser, DbSession
from app.models.user import User

router = APIRouter()


def _create_tokens(user_id: int) -> TokenResponse:
    """Generate an access + refresh token pair for a user."""
    data = {"sub": str(user_id)}
    return TokenResponse(
        access_token=create_access_token(data),
        refresh_token=create_refresh_token(data),
    )


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(body: UserCreate, session: DbSession) -> TokenResponse:
    """Register a new user and return JWT tokens."""
    # Check for existing email
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

    return _create_tokens(user.id)


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

    return _create_tokens(user.id)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(session: DbSession, token: str = Body(...)) -> TokenResponse:
    """Exchange a valid refresh token for a new token pair."""
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

    result = await session.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return _create_tokens(user.id)


@router.get("/me", response_model=UserResponse)
async def me(current_user: CurrentUser) -> UserResponse:
    """Return the authenticated user's profile."""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        created_at=current_user.created_at,
    )
