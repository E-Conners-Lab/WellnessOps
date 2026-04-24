"""
Scoring calibration service (Phase 6).
Tracks the delta between AI-generated scores and the practitioner's overrides.
Used to identify systematic bias in scoring prompts.
"""

import structlog
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.score import CategoryScore

logger = structlog.stdlib.get_logger()


async def get_calibration_stats(db: AsyncSession) -> dict:
    """Calculate calibration statistics across all audits."""
    # Get all scores with AI-generated values, grouped by category
    result = await db.execute(
        select(
            CategoryScore.category_key,
            CategoryScore.category_name,
            func.count(CategoryScore.id).label("total_scores"),
            func.sum(case((CategoryScore.practitioner_override.is_(True), 1), else_=0)).label("override_count"),
            func.avg(CategoryScore.ai_generated_score).label("avg_ai_score"),
            func.avg(CategoryScore.score).label("avg_final_score"),
        )
        .where(CategoryScore.ai_generated_score.isnot(None))
        .group_by(CategoryScore.category_key, CategoryScore.category_name)
        .order_by(CategoryScore.category_key)
    )

    categories = []
    for row in result:
        total = row.total_scores or 0
        overrides = int(row.override_count or 0)
        avg_ai = round(float(row.avg_ai_score or 0), 1)
        avg_final = round(float(row.avg_final_score or 0), 1)
        delta = round(avg_final - avg_ai, 1)

        categories.append({
            "category_key": row.category_key,
            "category_name": row.category_name,
            "total_scores": total,
            "override_count": overrides,
            "override_rate": round(overrides / total * 100, 1) if total > 0 else 0,
            "avg_ai_score": avg_ai,
            "avg_final_score": avg_final,
            "avg_delta": delta,
            "bias_direction": "over" if delta < 0 else "under" if delta > 0 else "aligned",
        })

    total_scores = sum(c["total_scores"] for c in categories)
    total_overrides = sum(c["override_count"] for c in categories)
    overall_override_rate = (
        round(total_overrides / total_scores * 100, 1) if total_scores > 0 else 0
    )

    biased = sorted(categories, key=lambda c: abs(c["avg_delta"]), reverse=True)

    return {
        "total_scores": total_scores,
        "total_overrides": total_overrides,
        "overall_override_rate": overall_override_rate,
        "categories": categories,
        "most_biased": biased[:3] if biased else [],
    }
