"""Category score schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ScoreOverride(BaseModel):
    """Override a category score."""

    score: int = Field(ge=1, le=10)
    override_notes: str | None = None


class CategoryScoreResponse(BaseModel):
    """Category score data returned from API."""

    id: uuid.UUID
    session_id: uuid.UUID
    category_key: str
    category_name: str
    score: int
    ai_generated_score: int | None = None
    status_label: str
    what_observed: str | None = None
    why_it_matters: str | None = None
    how_to_close_gap: str | None = None
    is_extended_category: bool
    practitioner_override: bool
    override_notes: str | None = None
    sort_order: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
