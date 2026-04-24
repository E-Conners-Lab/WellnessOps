"""
Report and score routes.
Generation, preview, editing, approval, PDF export, and score override.
Auth required (SEC-02). Session ownership verified (SEC-03).
"""

import os
from datetime import datetime, timezone
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import get_current_user
from app.db.database import get_db
from app.db.models.audit import AuditSession
from app.db.models.report import Report
from app.db.models.score import CategoryScore, get_score_label
from app.db.models.user import User
from app.schemas.common import APIResponse
from app.schemas.report import ReportResponse, ReportUpdate
from app.schemas.score import CategoryScoreResponse, ScoreOverride
from app.services.audit_logger import write_audit_log

logger = structlog.stdlib.get_logger()
router = APIRouter()


async def _get_session_owned(
    session_id: UUID, user: User, db: AsyncSession
) -> AuditSession:
    result = await db.execute(
        select(AuditSession).where(AuditSession.id == session_id)
    )
    session = result.scalar_one_or_none()
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not your session")
    return session


# --- Score routes ---

@router.get("/audits/{audit_id}/scores")
async def get_scores(
    audit_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    """Get all category scores for this session."""
    await _get_session_owned(audit_id, user, db)
    result = await db.execute(
        select(CategoryScore)
        .where(CategoryScore.session_id == audit_id)
        .order_by(CategoryScore.sort_order)
    )
    scores = result.scalars().all()
    return APIResponse(
        data=[CategoryScoreResponse.model_validate(s).model_dump() for s in scores]
    )


@router.post("/audits/{audit_id}/scores/generate")
async def generate_scores_endpoint(
    audit_id: UUID,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    """Trigger AI score generation using RAG + LLM."""
    session = await _get_session_owned(audit_id, user, db)

    # Delete existing scores for regeneration
    existing = await db.execute(
        select(CategoryScore).where(CategoryScore.session_id == audit_id)
    )
    for score in existing.scalars().all():
        await db.delete(score)
    await db.flush()

    from app.services.diagnosis import generate_scores

    scores = await generate_scores(db, str(audit_id), session.audit_tier)

    if session.status in ("in_progress", "observations_complete"):
        session.status = "diagnosis_pending"
        await db.flush()

    await write_audit_log(
        db, action="scores_generated", user_id=user.id,
        resource_type="audit_session", resource_id=audit_id, request=request,
    )

    return APIResponse(
        data=[CategoryScoreResponse.model_validate(s).model_dump() for s in scores]
    )


@router.put("/audits/{audit_id}/scores/{category_key}/override")
async def override_score(
    audit_id: UUID,
    category_key: str,
    body: ScoreOverride,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    """Override a category score with the practitioner's assessment."""
    await _get_session_owned(audit_id, user, db)

    result = await db.execute(
        select(CategoryScore).where(
            CategoryScore.session_id == audit_id,
            CategoryScore.category_key == category_key,
        )
    )
    score = result.scalar_one_or_none()
    if score is None:
        raise HTTPException(status_code=404, detail="Score not found")

    score.score = body.score
    score.status_label = get_score_label(body.score)
    score.practitioner_override = True
    score.override_notes = body.override_notes
    await db.flush()

    return APIResponse(data=CategoryScoreResponse.model_validate(score).model_dump())


# --- Report routes ---

@router.post("/audits/{audit_id}/reports/generate")
async def generate_report_endpoint(
    audit_id: UUID,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    """Generate a full client report from session data + RAG."""
    session = await _get_session_owned(audit_id, user, db)

    from app.services.report_generator import generate_report

    report = await generate_report(db, str(audit_id), str(user.id))

    if session.status in ("diagnosis_pending", "observations_complete"):
        session.status = "report_draft"
        await db.flush()

    await write_audit_log(
        db, action="report_generated", user_id=user.id,
        resource_type="report", resource_id=report.id, request=request,
    )

    return APIResponse(data=ReportResponse.model_validate(report).model_dump())


@router.get("/reports/{report_id}")
async def get_report(
    report_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    """Get full report content."""
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    await _get_session_owned(report.session_id, user, db)
    return APIResponse(data=ReportResponse.model_validate(report).model_dump())


@router.put("/reports/{report_id}")
async def update_report(
    report_id: UUID,
    body: ReportUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    """Edit report sections. The practitioner can modify any generated text."""
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    await _get_session_owned(report.session_id, user, db)

    if report.status == "final":
        raise HTTPException(status_code=400, detail="Cannot edit a finalized report")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(report, field, value)
    await db.flush()

    return APIResponse(data=ReportResponse.model_validate(report).model_dump())


@router.put("/reports/{report_id}/approve")
async def approve_report(
    report_id: UUID,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    """Approve and finalize report. Triggers PDF generation."""
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    session = await _get_session_owned(report.session_id, user, db)

    report.status = "final"
    report.approved_by = user.id
    report.approved_at = datetime.now(timezone.utc)
    await db.flush()

    try:
        from app.services.report_generator import generate_pdf
        await generate_pdf(db, report, str(report.session_id))
    except Exception:
        logger.exception("pdf_generation_failed", report_id=str(report_id))

    session.status = "report_final"
    await db.flush()

    # Extract patterns for future audits (Phase 5)
    try:
        from app.services.pattern_matcher import extract_patterns
        pattern_count = await extract_patterns(db, report.session_id)
        logger.info("patterns_extracted_on_approval", count=pattern_count)
    except Exception:
        logger.exception("pattern_extraction_failed_on_approval")

    await write_audit_log(
        db, action="report_approved", user_id=user.id,
        resource_type="report", resource_id=report.id, request=request,
    )

    return APIResponse(data=ReportResponse.model_validate(report).model_dump())


@router.get("/reports/{report_id}/pdf")
async def download_report_pdf(
    report_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Download the generated PDF."""
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    await _get_session_owned(report.session_id, user, db)

    if not report.pdf_path:
        raise HTTPException(status_code=404, detail="PDF not generated yet")

    full_path = os.path.join(settings.upload_dir, report.pdf_path)
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="PDF file not found")

    return FileResponse(
        full_path, media_type="application/pdf",
        filename=os.path.basename(report.pdf_path),
    )


@router.get("/reports/{report_id}/preview")
async def preview_report(
    report_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    """Get report data with scores for browser preview."""
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    await _get_session_owned(report.session_id, user, db)

    scores_result = await db.execute(
        select(CategoryScore)
        .where(CategoryScore.session_id == report.session_id)
        .order_by(CategoryScore.sort_order)
    )
    scores = scores_result.scalars().all()

    report_data = ReportResponse.model_validate(report).model_dump()
    report_data["scores"] = [
        CategoryScoreResponse.model_validate(s).model_dump() for s in scores
    ]
    return APIResponse(data=report_data)


# --- Pattern routes (Phase 5) ---

@router.get("/audits/{audit_id}/patterns")
async def get_session_patterns(
    audit_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    """Get pattern matches for each scored category in this session."""
    session = await _get_session_owned(audit_id, user, db)

    scores_result = await db.execute(
        select(CategoryScore)
        .where(CategoryScore.session_id == audit_id)
        .order_by(CategoryScore.sort_order)
    )
    scores = scores_result.scalars().all()

    from app.services.pattern_matcher import find_similar_patterns
    from app.schemas.pattern import PatternMatch

    category_patterns: dict[str, list] = {}
    for score in scores:
        obs_text = score.what_observed or score.category_name
        matches = find_similar_patterns(score.category_key, obs_text, top_k=3)
        if matches:
            category_patterns[score.category_key] = [
                PatternMatch(**m).model_dump() for m in matches
            ]

    return APIResponse(data=category_patterns)


@router.post("/patterns/search")
async def search_patterns(
    body: dict,
    user: User = Depends(get_current_user),
) -> APIResponse:
    """Search for similar patterns given observations text."""
    from app.services.pattern_matcher import find_similar_patterns, get_pattern_insights
    from app.schemas.pattern import PatternMatch

    text = body.get("observations_text", "")
    category = body.get("category_key")
    top_k = body.get("top_k", 5)

    if not text:
        return APIResponse(data=[])

    matches = find_similar_patterns(category, text, top_k=top_k)
    enriched = await get_pattern_insights(text, matches)

    return APIResponse(
        data=[PatternMatch(**m).model_dump() for m in enriched]
    )


@router.get("/audits/{audit_id}/referrals")
async def get_session_referrals(
    audit_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    """Get auto-matched product and partner referrals for this session's scores."""
    await _get_session_owned(audit_id, user, db)

    scores_result = await db.execute(
        select(CategoryScore)
        .where(CategoryScore.session_id == audit_id)
        .order_by(CategoryScore.sort_order)
    )
    scores = scores_result.scalars().all()

    if not scores:
        return APIResponse(data={"product_matches": {}, "partner_matches": {}})

    from app.services.referral_matcher import match_referrals
    referrals = await match_referrals(db, scores)
    return APIResponse(data=referrals)


@router.get("/calibration")
async def get_calibration(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    """Get scoring calibration stats: AI vsthe practitioner override deltas."""
    from app.services.calibration import get_calibration_stats
    stats = await get_calibration_stats(db)
    return APIResponse(data=stats)
