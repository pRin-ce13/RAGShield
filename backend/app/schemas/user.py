"""Pydantic Request and Response Schemas for User Accounts and Authentication."""

from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field


UserRoleType = Literal["admin", "analyst", "viewer"]


class UserBase(BaseModel):
    """Shared user attributes."""
    email: EmailStr
    full_name: Optional[str] = None
    role: UserRoleType = "analyst"


class UserCreate(UserBase):
    """Payload for registering a new user."""
    password: str = Field(..., min_length=8, description="Raw plaintext password to be hashed")


class UserUpdate(BaseModel):
    """Payload for updating an existing user profile."""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: Optional[UserRoleType] = None
    is_active: Optional[bool] = None
    password: Optional[str] = Field(None, min_length=8)


class UserLogin(BaseModel):
    """Payload for user authentication."""
    email: EmailStr
    password: str


class UserResponse(UserBase):
    """Public user profile response (password hash strictly omitted)."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class TokenResponse(BaseModel):
    """Bearer access token payload."""
    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int
    user: UserResponse


class TokenPayload(BaseModel):
    """Decoded JWT claims payload."""
    sub: str  # user id
    email: str
    role: str
    exp: int
