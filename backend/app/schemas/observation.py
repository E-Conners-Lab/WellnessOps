"""
Observation request and response schemas.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ObservationCreate(BaseModel):
    """Add a single observation."""

    room_area: str = Field(min_length=1, max_length=100)
    category: str | None = None
    observation_type: str = Field(default="text", pattern="^(text|photo|measurement|wearable_data)$")
    content: str | None = None
    photo_path: str | None = None
    is_from_structured_flow: bool = True
    domain_tags: list[str] | None = None
    sort_order: int = 0
    prompt_key: str | None = None
    skipped: bool = False


class ObservationUpdate(BaseModel):
    """Update an existing observation."""

    content: str | None = None
    photo_path: str | None = None
    category: str | None = None
    domain_tags: list[str] | None = None
    skipped: bool | None = None


class ObservationBulkItem(BaseModel):
    """Single item in a bulk observation submission."""

    room_area: str = Field(min_length=1, max_length=100)
    category: str | None = None
    observation_type: str = "text"
    content: str | None = None
    photo_path: str | None = None
    prompt_key: str | None = None
    skipped: bool = False
    sort_order: int = 0


class ObservationBulkCreate(BaseModel):
    """Bulk add observations from a completed room section."""

    observations: list[ObservationBulkItem] = Field(min_length=1)


class ObservationResponse(BaseModel):
    """Observation data returned from API."""

    id: uuid.UUID
    session_id: uuid.UUID
    room_area: str
    category: str | None = None
    observation_type: str
    content: str | None = None
    photo_path: str | None = None
    photo_thumbnail_path: str | None = None
    is_from_structured_flow: bool
    auto_categorized: bool
    domain_tags: list[str] | None = None
    sort_order: int
    prompt_key: str | None = None
    skipped: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
