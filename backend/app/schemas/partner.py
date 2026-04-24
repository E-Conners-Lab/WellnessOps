"""Partner schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class PartnerCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    business_name: str | None = None
    category: str = Field(min_length=1, max_length=100)
    location: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    website: str | None = None
    why_recommended: str = Field(min_length=1)
    best_for_client_type: str | None = None
    pricing_tier: str | None = None
    is_ambassador: bool = False
    practitioner_note: str | None = None


class PartnerUpdate(BaseModel):
    name: str | None = None
    business_name: str | None = None
    category: str | None = None
    location: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    website: str | None = None
    why_recommended: str | None = None
    best_for_client_type: str | None = None
    pricing_tier: str | None = None
    is_ambassador: bool | None = None
    practitioner_note: str | None = None
    is_active: bool | None = None


class PartnerResponse(BaseModel):
    id: uuid.UUID
    name: str
    business_name: str | None = None
    category: str
    location: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    website: str | None = None
    why_recommended: str
    best_for_client_type: str | None = None
    pricing_tier: str | None = None
    is_ambassador: bool
    practitioner_note: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
