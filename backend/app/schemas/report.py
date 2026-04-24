"""Report schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel


class ReportUpdate(BaseModel):
    """Edit report sections."""

    vision_section: str | None = None
    next_steps: str | None = None
    priority_action_plan: dict | None = None


class ReportResponse(BaseModel):
    """Report data returned from API."""

    id: uuid.UUID
    session_id: uuid.UUID
    version: int
    status: str
    overall_score: int
    overall_label: str
    priority_action_plan: dict | None = None
    vision_section: str | None = None
    next_steps: str | None = None
    pdf_path: str | None = None
    generated_by: str
    approved_by: uuid.UUID | None = None
    approved_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
