"""
Audit session routes.
Auth required on all endpoints (SEC-02).
Ownership verified on all operations (SEC-03, SEC-27).
"""

from datetime import datetime, timezone
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.prompts import get_sections_for_tier, get_total_prompts_for_tier, SECTION_BY_ROOM
from app.core.security import get_current_user
from app.db.database import get_db
from app.db.models.audit import AuditSession, STATUS_TRANSITIONS, VALID_STATUSES
from app.db.models.client import Client
from app.db.models.observation import Observation
from app.db.models.user import User
from app.schemas.audit import (
    AuditSessionCreate,
    AuditSessionResponse,
    AuditSessionUpdate,
    SectionProgress,
    SessionProgress,
    StatusAdvance,
)
from app.schemas.common import APIResponse
from app.schemas.observation import ObservationResponse
from app.services.audit_logger import write_audit_log

logger = structlog.stdlib.get_logger()
router = APIRouter()


async def _get_session_with_ownership(
    audit_id: UUID, user: User, db: AsyncSession
) -> AuditSession:
    """Fetch a session and verify the user owns the linked client (SEC-03)."""
    result = await db.execute(
        select(AuditSession).where(AuditSession.id == audit_id)
    )
    session = result.scalar_one_or_none()
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    if session.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your session")
    return session


@router.post("", status_code=201)
async def create_audit_session(
    body: AuditSessionCreate,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    """Start a new audit session linked to a client."""
    # Verify client ownership (SEC-27)
    result = await db.execute(
        select(Client).where(Client.id == body.client_id, Client.is_active.is_(True))
    )
    client = result.scalar_one_or_none()
    if client is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
    if client.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your client")

    session = AuditSession(
        client_id=body.client_id,
        user_id=user.id,
        audit_tier=body.audit_tier,
        notes=body.notes,
    )
    db.add(session)
    await db.flush()

    await write_audit_log(
        db,
        action="audit_session_create",
        user_id=user.id,
        resource_type="audit_session",
        resource_id=session.id,
        details={"client_id": str(body.client_id), "tier": body.audit_tier},
        request=request,
    )

    return APIResponse(data=AuditSessionResponse.model_validate(session).model_dump())


@router.get("/{audit_id}")
async def get_audit_session(
    audit_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    """Get audit session with all observations."""
    session = await _get_session_with_ownership(audit_id, user, db)

    result = await db.execute(
        select(Observation)
        .where(Observation.session_id == audit_id)
        .order_by(Observation.sort_order)
    )
    observations = result.scalars().all()

    session_data = AuditSessionResponse.model_validate(session).model_dump()
    session_data["observations"] = [
        ObservationResponse.model_validate(o).model_dump() for o in observations
    ]
    return APIResponse(data=session_data)


@router.put("/{audit_id}")
async def update_audit_session(
    audit_id: UUID,
    body: AuditSessionUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    """Update session metadata (tier, notes)."""
    session = await _get_session_with_ownership(audit_id, user, db)

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(session, field, value)
    await db.flush()

    return APIResponse(data=AuditSessionResponse.model_validate(session).model_dump())


@router.put("/{audit_id}/status")
async def advance_session_status(
    audit_id: UUID,
    body: StatusAdvance,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    """Advance session status through the workflow."""
    session = await _get_session_with_ownership(audit_id, user, db)

    if body.target_status not in VALID_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status: {body.target_status}",
        )

    expected_next = STATUS_TRANSITIONS.get(session.status)
    if body.target_status != expected_next:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot transition from '{session.status}' to '{body.target_status}'. Next valid status: '{expected_next}'",
        )

    session.status = body.target_status
    if body.target_status == "closed":
        session.completed_at = datetime.now(timezone.utc)
    await db.flush()

    await write_audit_log(
        db,
        action="audit_session_status_change",
        user_id=user.id,
        resource_type="audit_session",
        resource_id=session.id,
        details={"new_status": body.target_status},
        request=request,
    )

    return APIResponse(data=AuditSessionResponse.model_validate(session).model_dump())


@router.get("/{audit_id}/progress")
async def get_session_progress(
    audit_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    """Get completion progress by room/section for Field Companion UI."""
    session = await _get_session_with_ownership(audit_id, user, db)

    # Get all observations for this session
    result = await db.execute(
        select(Observation).where(Observation.session_id == audit_id)
    )
    observations = result.scalars().all()

    # Build lookup of prompt_key -> observation
    answered_keys: set[str] = set()
    skipped_keys: set[str] = set()
    for obs in observations:
        if obs.prompt_key:
            if obs.skipped:
                skipped_keys.add(obs.prompt_key)
            else:
                answered_keys.add(obs.prompt_key)

    sections = get_sections_for_tier(session.audit_tier)
    section_progress: list[SectionProgress] = []
    total_prompts = 0
    total_completed = 0
    total_skipped = 0

    for sec in sections:
        sec_completed = sum(1 for p in sec.prompts if p.key in answered_keys)
        sec_skipped = sum(1 for p in sec.prompts if p.key in skipped_keys)
        section_progress.append(SectionProgress(
            room_area=sec.room_area,
            label=sec.label,
            total_prompts=len(sec.prompts),
            completed_prompts=sec_completed,
            skipped_prompts=sec_skipped,
        ))
        total_prompts += len(sec.prompts)
        total_completed += sec_completed
        total_skipped += sec_skipped

    addressed = total_completed + total_skipped
    pct = (addressed / total_prompts * 100) if total_prompts > 0 else 0

    progress = SessionProgress(
        total_prompts=total_prompts,
        completed_prompts=total_completed,
        skipped_prompts=total_skipped,
        completion_percent=round(pct, 1),
        sections=section_progress,
    )

    return APIResponse(data=progress.model_dump())


@router.get("/{audit_id}/prompts")
async def get_session_prompts(
    audit_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    """Get all prompt definitions for this session's tier."""
    session = await _get_session_with_ownership(audit_id, user, db)
    sections = get_sections_for_tier(session.audit_tier)

    return APIResponse(data=[
        {
            "room_area": sec.room_area,
            "label": sec.label,
            "tier": sec.tier,
            "prompts": [
                {"key": p.key, "text": p.text, "sort_order": p.sort_order}
                for p in sec.prompts
            ],
        }
        for sec in sections
    ])
