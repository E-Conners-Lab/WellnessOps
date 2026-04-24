"""
Immutable audit log writer (SEC-28).
Write-only service. Logs auth events, data access, admin actions, and knowledge operations.
"""

import uuid

import structlog
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.audit_log import AuditLog

logger = structlog.stdlib.get_logger()


async def write_audit_log(
    db: AsyncSession,
    *,
    action: str,
    user_id: uuid.UUID | None = None,
    resource_type: str | None = None,
    resource_id: uuid.UUID | None = None,
    details: dict | None = None,
    request: Request | None = None,
) -> None:
    """Write an immutable audit log entry.

    Never raises -- logs failures but does not block the calling operation.
    """
    try:
        ip_address = None
        user_agent = None
        if request is not None:
            ip_address = request.client.host if request.client else None
            user_agent = request.headers.get("user-agent")

        entry = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        db.add(entry)
        await db.flush()
        logger.info(
            "audit_log_written",
            action=action,
            resource_type=resource_type,
            user_id=str(user_id) if user_id else None,
        )
    except Exception:
        logger.exception("audit_log_write_failed", action=action)
