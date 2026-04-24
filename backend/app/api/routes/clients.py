"""
Client management routes.
Auth required on all endpoints (SEC-02).
Ownership verified on all operations (SEC-03, SEC-27).
PII gated by consent flag -- stripped from responses when consent is false.
"""

from datetime import datetime, timezone
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.database import get_db
from app.db.models.client import Client, PII_FIELDS
from app.db.models.audit import AuditSession
from app.db.models.observation import Observation
from app.db.models.user import User
from app.schemas.client import ClientCreate, ClientResponse, ClientUpdate, PII_FIELD_NAMES
from app.schemas.common import APIResponse
from app.services.audit_logger import write_audit_log

logger = structlog.stdlib.get_logger()
router = APIRouter()


def _client_response(client: Client) -> dict:
    """Build a client response dict with PII decryption and consent gating."""
    from app.core.encryption import decrypt_pii
    from app.db.models.client import PII_FIELDS as PII_MODEL_FIELDS, _looks_encrypted

    # Ensure PII fields are decrypted (may still be encrypted in-memory after insert)
    data = ClientResponse.model_validate(client).model_dump()
    for field in PII_MODEL_FIELDS:
        val = data.get(field)
        if val is not None and isinstance(val, str) and _looks_encrypted(val):
            try:
                data[field] = decrypt_pii(val)
            except Exception:
                data[field] = None

    response = ClientResponse(**data)
    return response.strip_pii().model_dump()


async def _get_client_with_ownership(
    client_id: UUID,
    user: User,
    db: AsyncSession,
) -> Client:
    """Fetch a client and verify ownership (SEC-03, SEC-27)."""
    result = await db.execute(
        select(Client).where(Client.id == client_id, Client.is_active.is_(True))
    )
    client = result.scalar_one_or_none()
    if client is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
    if client.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your client")
    return client


@router.get("")
async def list_clients(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    """List all active clients for the authenticated user."""
    result = await db.execute(
        select(Client)
        .where(Client.user_id == user.id, Client.is_active.is_(True))
        .order_by(Client.display_name)
    )
    clients = result.scalars().all()
    return APIResponse(data=[_client_response(c) for c in clients])


@router.post("", status_code=201)
async def create_client(
    body: ClientCreate,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    """Create a new client profile. PII rejected unless pii_consent is true."""
    client = Client(user_id=user.id, **body.model_dump())
    db.add(client)
    await db.flush()

    await write_audit_log(
        db,
        action="client_create",
        user_id=user.id,
        resource_type="client",
        resource_id=client.id,
        details={"display_name": client.display_name},
        request=request,
    )

    return APIResponse(data=_client_response(client))


@router.get("/{client_id}")
async def get_client(
    client_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    """Get client details. PII stripped if consent is false. Verify ownership (SEC-03)."""
    client = await _get_client_with_ownership(client_id, user, db)
    return APIResponse(data=_client_response(client))


@router.put("/{client_id}")
async def update_client(
    client_id: UUID,
    body: ClientUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    """Update client profile. PII updates rejected if consent is false (SEC-03)."""
    client = await _get_client_with_ownership(client_id, user, db)

    update_data = body.model_dump(exclude_unset=True)

    # If setting pii_consent to false, clear existing PII
    if "pii_consent" in update_data and not update_data["pii_consent"]:
        for field in PII_FIELD_NAMES:
            setattr(client, field, None)
            update_data.pop(field, None)

    # Block PII updates if consent is not granted
    if not client.pii_consent and "pii_consent" not in update_data:
        for field in PII_FIELD_NAMES:
            if field in update_data and update_data[field] is not None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cannot store '{field}' without PII consent",
                )

    for field, value in update_data.items():
        setattr(client, field, value)
    await db.flush()

    return APIResponse(data=_client_response(client))


@router.delete("/{client_id}")
async def delete_client(
    client_id: UUID,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    """Soft delete client. Verify ownership (SEC-03)."""
    client = await _get_client_with_ownership(client_id, user, db)
    client.is_active = False
    await db.flush()

    await write_audit_log(
        db,
        action="client_delete",
        user_id=user.id,
        resource_type="client",
        resource_id=client.id,
        request=request,
    )

    return APIResponse(data={"message": "Client deleted"})


@router.get("/{client_id}/sessions")
async def list_client_sessions(
    client_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    """List all audit sessions for a client."""
    await _get_client_with_ownership(client_id, user, db)

    result = await db.execute(
        select(AuditSession)
        .where(AuditSession.client_id == client_id)
        .order_by(AuditSession.started_at.desc())
    )
    sessions = result.scalars().all()

    from app.schemas.audit import AuditSessionResponse

    return APIResponse(
        data=[AuditSessionResponse.model_validate(s).model_dump() for s in sessions]
    )


@router.post("/{client_id}/export")
async def export_client_data(
    client_id: UUID,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    """Export all client data for portability (GDPR Article 20)."""
    client = await _get_client_with_ownership(client_id, user, db)

    # Gather all sessions and observations
    sessions_result = await db.execute(
        select(AuditSession).where(AuditSession.client_id == client_id)
    )
    sessions = sessions_result.scalars().all()

    from app.schemas.audit import AuditSessionResponse
    from app.schemas.observation import ObservationResponse

    export_sessions = []
    for session in sessions:
        obs_result = await db.execute(
            select(Observation).where(Observation.session_id == session.id)
        )
        observations = obs_result.scalars().all()

        session_data = AuditSessionResponse.model_validate(session).model_dump()
        session_data["observations"] = [
            ObservationResponse.model_validate(o).model_dump() for o in observations
        ]
        export_sessions.append(session_data)

    export = {
        "client": _client_response(client),
        "sessions": export_sessions,
        "exported_at": str(datetime.now(timezone.utc)),
    }

    await write_audit_log(
        db,
        action="client_data_export",
        user_id=user.id,
        resource_type="client",
        resource_id=client.id,
        request=request,
    )

    return APIResponse(data=export)


@router.delete("/{client_id}/purge")
async def purge_client(
    client_id: UUID,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    """Hard-delete a client and ALL related data (GDPR Article 17).

    This permanently removes: the client record, all audit sessions,
    all observations, and any uploaded files. This action is irreversible.
    """
    client = await _get_client_with_ownership(client_id, user, db)

    # Delete observations for all sessions
    sessions_result = await db.execute(
        select(AuditSession).where(AuditSession.client_id == client_id)
    )
    sessions = sessions_result.scalars().all()

    for session in sessions:
        await db.execute(
            select(Observation).where(Observation.session_id == session.id)
        )
        # Delete observations
        obs_result = await db.execute(
            select(Observation).where(Observation.session_id == session.id)
        )
        for obs in obs_result.scalars().all():
            await db.delete(obs)

        # Delete session
        await db.delete(session)

    # Delete client
    await db.delete(client)

    await write_audit_log(
        db,
        action="client_purge",
        user_id=user.id,
        resource_type="client",
        resource_id=client_id,
        details={"display_name": client.display_name, "purged": True},
        request=request,
    )

    logger.info("client_purged", client_id=str(client_id))
    return APIResponse(data={"message": "Client and all related data permanently deleted"})
