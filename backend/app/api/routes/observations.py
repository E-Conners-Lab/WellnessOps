"""
Observation routes -- the core data capture layer.
Handles both structured (Field Companion) and free-form input.
Auth required (SEC-02). Session ownership verified (SEC-03).
"""

import os
import uuid
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import get_current_user
from app.db.database import get_db
from app.db.models.audit import AuditSession
from app.db.models.observation import Observation
from app.db.models.user import User
from app.schemas.categorize import CategorizeItem, CategorizeRequest
from app.schemas.common import APIResponse
from app.schemas.observation import (
    ObservationBulkCreate,
    ObservationCreate,
    ObservationResponse,
    ObservationUpdate,
)
from app.services.file_handler import FileValidationError, strip_exif, validate_file

logger = structlog.stdlib.get_logger()
router = APIRouter()


async def _verify_session_ownership(
    audit_id: UUID, user: User, db: AsyncSession
) -> AuditSession:
    """Verify the user owns the session (SEC-03)."""
    result = await db.execute(
        select(AuditSession).where(AuditSession.id == audit_id)
    )
    session = result.scalar_one_or_none()
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    if session.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your session")
    if session.status != "in_progress":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session is not in progress",
        )
    return session


@router.post("/audits/{audit_id}/observations", status_code=201)
async def add_observation(
    audit_id: UUID,
    body: ObservationCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    """Add a single observation to an audit session."""
    await _verify_session_ownership(audit_id, user, db)

    obs = Observation(
        session_id=audit_id,
        **body.model_dump(),
    )
    db.add(obs)
    await db.flush()

    return APIResponse(data=ObservationResponse.model_validate(obs).model_dump())


@router.put("/observations/{observation_id}")
async def update_observation(
    observation_id: UUID,
    body: ObservationUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    """Edit an existing observation."""
    obs = await _get_observation_with_ownership(observation_id, user, db)

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(obs, field, value)
    await db.flush()

    return APIResponse(data=ObservationResponse.model_validate(obs).model_dump())


@router.delete("/observations/{observation_id}")
async def delete_observation(
    observation_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    """Delete an observation."""
    obs = await _get_observation_with_ownership(observation_id, user, db)
    await db.delete(obs)
    return APIResponse(data={"message": "Observation deleted"})


@router.post("/audits/{audit_id}/observations/bulk", status_code=201)
async def bulk_add_observations(
    audit_id: UUID,
    body: ObservationBulkCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    """Bulk add observations from a completed room section."""
    await _verify_session_ownership(audit_id, user, db)

    created = []
    for item in body.observations:
        obs = Observation(
            session_id=audit_id,
            is_from_structured_flow=True,
            **item.model_dump(),
        )
        db.add(obs)
        created.append(obs)

    await db.flush()

    return APIResponse(
        data=[ObservationResponse.model_validate(o).model_dump() for o in created]
    )


@router.post("/audits/{audit_id}/photos", status_code=201)
async def upload_photo(
    audit_id: UUID,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    """Upload a photo for an audit session.

    Validates file type/size (SEC-22), strips EXIF metadata (SEC-21),
    generates a thumbnail, and returns the file paths.
    """
    await _verify_session_ownership(audit_id, user, db)

    content = await file.read()

    try:
        validate_file(content, file.filename or "photo.jpg", file.content_type or "")
    except FileValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc

    # Strip EXIF metadata (SEC-21)
    cleaned = strip_exif(content)

    # Save to upload directory
    session_dir = os.path.join(settings.upload_dir, str(audit_id))
    os.makedirs(session_dir, exist_ok=True)

    photo_id = str(uuid.uuid4())
    ext = (file.filename or "photo.jpg").rsplit(".", 1)[-1].lower()
    photo_filename = f"{photo_id}.{ext}"
    thumb_filename = f"{photo_id}_thumb.{ext}"

    photo_path = os.path.join(session_dir, photo_filename)
    thumb_path = os.path.join(session_dir, thumb_filename)

    with open(photo_path, "wb") as f:
        f.write(cleaned)

    # Generate thumbnail
    try:
        from PIL import Image
        import io

        img = Image.open(io.BytesIO(cleaned))
        img.thumbnail((400, 400))
        img.save(thumb_path)
    except Exception:
        logger.exception("thumbnail_generation_failed")
        thumb_path = photo_path  # fallback to full image

    # Return relative paths for storage in observation records
    rel_photo = f"{audit_id}/{photo_filename}"
    rel_thumb = f"{audit_id}/{thumb_filename}"

    return APIResponse(data={
        "photo_path": rel_photo,
        "thumbnail_path": rel_thumb,
    })


@router.post("/audits/{audit_id}/photos/analyze", status_code=200)
async def upload_and_analyze_photo(
    audit_id: UUID,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    """Upload a photo, analyze it with vision AI, and return the description + paths.

    Combines photo upload (EXIF strip, validation, thumbnail) with
    vision model analysis to auto-generate observation text from the image.
    """
    await _verify_session_ownership(audit_id, user, db)

    content = await file.read()

    try:
        validate_file(content, file.filename or "photo.jpg", file.content_type or "")
    except FileValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc

    # Strip EXIF (SEC-21)
    cleaned = strip_exif(content)

    # Save photo and thumbnail
    session_dir = os.path.join(settings.upload_dir, str(audit_id))
    os.makedirs(session_dir, exist_ok=True)

    photo_id = str(uuid.uuid4())
    ext = (file.filename or "photo.jpg").rsplit(".", 1)[-1].lower()
    photo_filename = f"{photo_id}.{ext}"
    thumb_filename = f"{photo_id}_thumb.{ext}"

    photo_path = os.path.join(session_dir, photo_filename)
    thumb_path = os.path.join(session_dir, thumb_filename)

    with open(photo_path, "wb") as f:
        f.write(cleaned)

    try:
        from PIL import Image
        import io as _io

        img = Image.open(_io.BytesIO(cleaned))
        img.thumbnail((400, 400))
        img.save(thumb_path)
    except Exception:
        logger.exception("thumbnail_generation_failed")

    rel_photo = f"{audit_id}/{photo_filename}"
    rel_thumb = f"{audit_id}/{thumb_filename}"

    # Vision analysis
    description = ""
    try:
        from app.services.vision import analyze_image
        description = await analyze_image(cleaned)
    except Exception:
        logger.exception("vision_analysis_failed")
        description = "Photo uploaded. Vision analysis unavailable."

    return APIResponse(data={
        "photo_path": rel_photo,
        "thumbnail_path": rel_thumb,
        "description": description,
    })


@router.post("/observations/categorize")
async def categorize_observation(
    body: CategorizeRequest,
    user: User = Depends(get_current_user),
) -> APIResponse:
    """Auto-categorize a free-form observation using the configured LLM.

    Returns a list of categorizations. If the input covers multiple rooms,
    each room gets its own entry with the relevant text extracted.
    """
    from app.services.categorizer import categorize_text

    results = await categorize_text(body.text)
    return APIResponse(
        data=[CategorizeItem(**r).model_dump() for r in results]
    )


async def _get_observation_with_ownership(
    observation_id: UUID, user: User, db: AsyncSession
) -> Observation:
    """Fetch observation and verify the user owns the parent session."""
    result = await db.execute(
        select(Observation).where(Observation.id == observation_id)
    )
    obs = result.scalar_one_or_none()
    if obs is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Observation not found")

    # Verify session ownership
    session_result = await db.execute(
        select(AuditSession).where(AuditSession.id == obs.session_id)
    )
    session = session_result.scalar_one_or_none()
    if session is None or session.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your observation")

    return obs
