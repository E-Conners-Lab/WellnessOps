"""
Audit session request and response schemas.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class AuditSessionCreate(BaseModel):
    """Start a new audit session."""

    client_id: uuid.UUID
    audit_tier: str = Field(default="core", pattern="^(core|extended)$")
    notes: str | None = None


class AuditSessionUpdate(BaseModel):
    """Update session metadata."""

    notes: str | None = None
    audit_tier: str | None = Field(default=None, pattern="^(core|extended)$")


class StatusAdvance(BaseModel):
    """Advance session to next status."""

    target_status: str


class AuditSessionResponse(BaseModel):
    """Audit session data returned from API."""

    id: uuid.UUID
    client_id: uuid.UUID
    user_id: uuid.UUID
    audit_tier: str
    status: str
    started_at: datetime
    completed_at: datetime | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SessionProgress(BaseModel):
    """Progress breakdown by room section."""

    total_prompts: int
    completed_prompts: int
    skipped_prompts: int
    completion_percent: float
    sections: list["SectionProgress"]


class SectionProgress(BaseModel):
    """Progress for a single room section."""

    room_area: str
    label: str
    total_prompts: int
    completed_prompts: int
    skipped_prompts: int
