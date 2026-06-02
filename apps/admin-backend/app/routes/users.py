"""Admin user management routes."""

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, or_, select

from starter_shared.security import hash_password
from starter_shared.types.user import (
    AdminUserCreate,
    UserResponse,
    UserRole,
    UserRoleUpdate,
)

from app.dependencies import CurrentUser, DbSession
from app.models.user import User

router = APIRouter()


@router.get("/", response_model=list[UserResponse])
async def list_users(
    session: DbSession,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 50,
    search: str | None = None,
    role: UserRole | None = None,
) -> list[UserResponse]:
    """List all users with optional search/filter/pagination."""
    query = select(User)
    if search:
        query = query.where(or_(User.email.ilike(f"%{search}%"), User.name.ilike(f"%{search}%")))
    if role:
        query = query.where(User.role == role)
    query = query.order_by(User.created_at.desc()).offset(skip).limit(limit)
    result = await session.execute(query)
    users = result.scalars().all()
    return [
        UserResponse(id=u.id, email=u.email, name=u.name, role=u.role, created_at=u.created_at)
        for u in users
    ]


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, session: DbSession, current_user: CurrentUser) -> UserResponse:
    """Get a single user by ID."""
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse(
        id=user.id, email=user.email, name=user.name, role=user.role, created_at=user.created_at
    )


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    body: AdminUserCreate,
    session: DbSession,
    current_user: CurrentUser,
) -> UserResponse:
    """Admin creates a new user account."""
    result = await session.execute(select(User).where(User.email == body.email))
    if result.scalar_one_or_none() is not None:
        raise HTTPException(status_code=409, detail="Email already registered")

    user = User(
        email=body.email,
        name=body.name,
        hashed_password=hash_password(body.password),
        role=body.role,
    )
    session.add(user)
    await session.flush()
    await session.refresh(user)
    return UserResponse(
        id=user.id, email=user.email, name=user.name, role=user.role, created_at=user.created_at
    )


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user_role(
    user_id: int,
    body: UserRoleUpdate,
    session: DbSession,
    current_user: CurrentUser,
) -> UserResponse:
    """Update a user's role. Cannot demote yourself."""
    if user_id == current_user.id and body.role != UserRole.admin:
        raise HTTPException(status_code=400, detail="Cannot change your own role")

    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    # Prevent demoting the last admin
    if user.role == UserRole.admin and body.role != UserRole.admin:
        admin_count = (
            await session.scalar(select(func.count(User.id)).where(User.role == UserRole.admin))
        ) or 0
        if admin_count <= 1:
            raise HTTPException(status_code=400, detail="Cannot demote the last admin")

    user.role = body.role
    await session.flush()
    await session.refresh(user)
    return UserResponse(
        id=user.id, email=user.email, name=user.name, role=user.role, created_at=user.created_at
    )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    session: DbSession,
    current_user: CurrentUser,
) -> None:
    """Delete a user. Cannot delete yourself."""
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")

    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    await session.delete(user)
