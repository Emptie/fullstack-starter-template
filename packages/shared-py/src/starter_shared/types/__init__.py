"""Shared Pydantic types — single source of truth for the type bridge."""

from starter_shared.types.admin import DashboardStats, PaginatedUserResponse
from starter_shared.types.health import HealthCheck
from starter_shared.types.user import (
    AdminUserCreate,
    ForgotPassword,
    PasswordChange,
    ResetPassword,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
    UserRole,
    UserRoleUpdate,
    UserUpdate,
    UserUpdateAdmin,
)

__all__ = [
    "AdminUserCreate",
    "DashboardStats",
    "ForgotPassword",
    "HealthCheck",
    "PaginatedUserResponse",
    "PasswordChange",
    "ResetPassword",
    "TokenResponse",
    "UserCreate",
    "UserLogin",
    "UserResponse",
    "UserRole",
    "UserRoleUpdate",
    "UserUpdate",
    "UserUpdateAdmin",
]
