"""
Authentication request and response schemas.
Server-side validation enforced (SEC-05).
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """Login request. Server-side validated (SEC-05)."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserResponse(BaseModel):
    """Public user data returned after login or user lookup."""

    id: uuid.UUID
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenPayload(BaseModel):
    """Decoded JWT payload."""

    sub: str
    role: str | None = None
    type: str
    exp: datetime
    jti: str
