"""Admin user management routes."""

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, or_, select

from starter_shared.security import hash_password
from starter_shared.types.admin import PaginatedUserResponse
from starter_shared.types.user import (
    AdminUserCreate,
    UserResponse,
    UserRole,
    UserUpdateAdmin,
)

from app.dependencies import CurrentUser, DbSession
from app.models.user import User

router = APIRouter()


def _user_to_response(u: User) -> UserResponse:
    return UserResponse(
        id=u.id, email=u.email, name=u.name, role=u.role, created_at=u.created_at
    )


@router.get("/", response_model=PaginatedUserResponse)
async def list_users(
    session: DbSession,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 50,
    search: str | None = None,
    role: UserRole | None = None,
) -> PaginatedUserResponse:
    """List all users with optional search/filter/pagination."""
    # Count query (no offset/limit)
    count_query = select(func.count(User.id))
    if search:
        count_query = count_query.where(
            or_(User.email.ilike(f"%{search}%"), User.name.ilike(f"%{search}%"))
        )
    if role:
        count_query = count_query.where(User.role == role)
    total = (await session.scalar(count_query)) or 0

    # Data query
    query = select(User)
    if search:
        query = query.where(
            or_(User.email.ilike(f"%{search}%"), User.name.ilike(f"%{search}%"))
        )
    if role:
        query = query.where(User.role == role)
    query = query.order_by(User.created_at.desc()).offset(skip).limit(limit)
    result = await session.execute(query)
    users = result.scalars().all()

    return PaginatedUserResponse(
        items=[_user_to_response(u) for u in users],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, session: DbSession, current_user: CurrentUser) -> UserResponse:
    """Get a single user by ID."""
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return _user_to_response(user)


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
    return _user_to_response(user)


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    body: UserUpdateAdmin,
    session: DbSession,
    current_user: CurrentUser,
) -> UserResponse:
    """Update a user's name, email, and/or role.

    Cannot demote yourself or the last admin.
    """
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    # Prevent demoting yourself
    if user_id == current_user.id and body.role != UserRole.admin:
        raise HTTPException(status_code=400, detail="Cannot change your own role")

    # Prevent demoting the last admin
    if user.role == UserRole.admin and body.role != UserRole.admin:
        admin_count = (
            await session.scalar(select(func.count(User.id)).where(User.role == UserRole.admin))
        ) or 0
        if admin_count <= 1:
            raise HTTPException(status_code=400, detail="Cannot demote the last admin")

    # Check email uniqueness if changing
    if body.email != user.email:
        existing = await session.scalar(
            select(func.count(User.id)).where(User.email == body.email)
        )
        if existing:
            raise HTTPException(status_code=409, detail="Email already registered")

    user.name = body.name
    user.email = body.email
    user.role = body.role
    await session.flush()
    await session.refresh(user)
    return _user_to_response(user)


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
