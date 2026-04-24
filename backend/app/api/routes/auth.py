"""
Authentication routes.
- JWT in httpOnly cookies (SEC-01)
- Rate limited (SEC-06)
- Session regeneration on login (SEC-04)
- Argon2id password hashing (SEC-17)
- Refresh token rotation (SEC-16)
"""

import uuid

import structlog
from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    clear_auth_cookies,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user,
    set_auth_cookies,
    verify_password,
)
from app.db.database import get_db
from app.db.models.user import User
from app.schemas.auth import LoginRequest, UserResponse
from app.schemas.common import APIResponse
from app.services.audit_logger import write_audit_log

logger = structlog.stdlib.get_logger()
router = APIRouter()


@router.post("/login")
async def login(
    credentials: LoginRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    """Authenticate user, issue JWT pair in httpOnly cookies (SEC-01, SEC-17)."""
    result = await db.execute(select(User).where(User.email == credentials.email))
    user = result.scalar_one_or_none()

    if user is None or not verify_password(credentials.password, user.password_hash):
        await write_audit_log(
            db,
            action="login_failed",
            details={"email": credentials.email},
            request=request,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled",
        )

    access_token = create_access_token(user.id, user.role)
    refresh_token = create_refresh_token(user.id)
    set_auth_cookies(response, access_token, refresh_token)

    await write_audit_log(
        db,
        action="login_success",
        user_id=user.id,
        request=request,
    )

    logger.info("user_logged_in", user_id=str(user.id))
    return APIResponse(data=UserResponse.model_validate(user).model_dump())


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    """Clear auth cookies and log the event (SEC-28)."""
    clear_auth_cookies(response)
    await write_audit_log(
        db,
        action="logout",
        user_id=user.id,
        request=request,
    )
    logger.info("user_logged_out", user_id=str(user.id))
    return APIResponse(data={"message": "Logged out"})


@router.post("/refresh")
async def refresh(
    request: Request,
    response: Response,
    refresh_token: str | None = Cookie(default=None),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    """Rotate refresh token and issue new access token (SEC-16)."""
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No refresh token",
        )

    payload = decode_token(refresh_token)

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    user_id = payload.get("sub")
    result = await db.execute(
        select(User).where(User.id == uuid.UUID(user_id), User.is_active.is_(True))
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    new_access = create_access_token(user.id, user.role)
    new_refresh = create_refresh_token(user.id)
    set_auth_cookies(response, new_access, new_refresh)

    await write_audit_log(
        db,
        action="token_refresh",
        user_id=user.id,
        request=request,
    )

    return APIResponse(data=UserResponse.model_validate(user).model_dump())


@router.get("/me")
async def get_me(user: User = Depends(get_current_user)) -> APIResponse:
    """Get the currently authenticated user's profile."""
    return APIResponse(data=UserResponse.model_validate(user).model_dump())
