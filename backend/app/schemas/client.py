"""
Client request and response schemas.
PII fields gated by consent flag -- stripped from responses when consent is false.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field, model_validator


PII_FIELD_NAMES = ("full_name", "email", "phone", "address")


class ClientCreate(BaseModel):
    """Create a new client. PII fields rejected unless pii_consent is true."""

    display_name: str = Field(min_length=1, max_length=255)
    full_name: str | None = None
    email: str | None = None
    phone: str | None = None
    address: str | None = None
    pii_consent: bool = False
    notes: str | None = None
    budget_tier: str | None = None
    has_wearable: bool = False
    wearable_type: str | None = None
    financial_audit_consent: bool = False

    @model_validator(mode="after")
    def reject_pii_without_consent(self):
        """Block PII fields if consent is not given."""
        if not self.pii_consent:
            for field in PII_FIELD_NAMES:
                if getattr(self, field) is not None:
                    raise ValueError(
                        f"Cannot store '{field}' without PII consent. "
                        "Set pii_consent to true or remove PII fields."
                    )
        return self


class ClientUpdate(BaseModel):
    """Update an existing client. All fields optional."""

    display_name: str | None = None
    full_name: str | None = None
    email: str | None = None
    phone: str | None = None
    address: str | None = None
    pii_consent: bool | None = None
    notes: str | None = None
    budget_tier: str | None = None
    has_wearable: bool | None = None
    wearable_type: str | None = None
    financial_audit_consent: bool | None = None


class ClientResponse(BaseModel):
    """Client data returned from API. PII stripped when consent is false."""

    id: uuid.UUID
    user_id: uuid.UUID
    display_name: str
    full_name: str | None = None
    email: str | None = None
    phone: str | None = None
    address: str | None = None
    pii_consent: bool
    notes: str | None = None
    budget_tier: str | None = None
    has_wearable: bool
    wearable_type: str | None = None
    financial_audit_consent: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    def strip_pii(self) -> "ClientResponse":
        """Return a copy with PII fields nulled out if consent is false."""
        if self.pii_consent:
            return self
        data = self.model_dump()
        for field in PII_FIELD_NAMES:
            data[field] = None
        return ClientResponse(**data)
