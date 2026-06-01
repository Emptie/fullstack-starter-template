"""User-related Pydantic schemas.

These models are the single source of truth for the type bridge.
After modifying, run `make generate` to update TypeScript types.
"""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    """Schema for user registration requests."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    name: str = Field(min_length=1, max_length=64)


class UserLogin(BaseModel):
    """Schema for user login requests."""

    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Schema for user data returned in API responses.

    Never includes the hashed password.
    """

    id: int
    email: str
    name: str
    created_at: datetime


class TokenResponse(BaseModel):
    """Schema for JWT token pairs returned after login/register/refresh."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
