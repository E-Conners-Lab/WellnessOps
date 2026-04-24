"""
Shared API dependencies for query optimization and common patterns.
"""

import uuid

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import get_current_user
from app.db.database import get_db
from app.db.models.audit import AuditSession
from app.db.models.client import Client
from app.db.models.user import User


async def get_session_with_client(
    audit_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AuditSession:
    """Load a session with client eagerly loaded. Verifies ownership."""
    result = await db.execute(
        select(AuditSession)
        .options(selectinload(AuditSession.client))
        .where(AuditSession.id == audit_id)
    )
    session = result.scalar_one_or_none()
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    if session.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your session")
    return session
