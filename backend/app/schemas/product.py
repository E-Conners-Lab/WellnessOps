"""Product schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    brand: str | None = None
    category: str = Field(min_length=1, max_length=100)
    price_range: str | None = None
    purchase_link: str | None = None
    why_recommended: str = Field(min_length=1)
    best_for: str | None = None
    contraindications: str | None = None
    practitioner_note: str | None = None
    is_recommended: bool = True
    not_recommended_reason: str | None = None


class ProductUpdate(BaseModel):
    name: str | None = None
    brand: str | None = None
    category: str | None = None
    price_range: str | None = None
    purchase_link: str | None = None
    why_recommended: str | None = None
    best_for: str | None = None
    contraindications: str | None = None
    practitioner_note: str | None = None
    is_recommended: bool | None = None
    not_recommended_reason: str | None = None
    is_active: bool | None = None


class ProductResponse(BaseModel):
    id: uuid.UUID
    name: str
    brand: str | None = None
    category: str
    price_range: str | None = None
    purchase_link: str | None = None
    why_recommended: str
    best_for: str | None = None
    contraindications: str | None = None
    practitioner_note: str | None = None
    is_recommended: bool
    not_recommended_reason: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
