"""
Client model. PII stored only with consent (pii_consent flag).
PII fields encrypted at rest with AES-256-GCM.
Ownership enforced via user_id (SEC-03, SEC-27).
"""

import uuid

from sqlalchemy import Boolean, ForeignKey, String, Text, Uuid, event
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models.base import Base, TimestampMixin, UUIDMixin

# PII fields that get encrypted at rest
PII_FIELDS = ("full_name", "email", "phone", "address")


class Client(Base, UUIDMixin, TimestampMixin):
    """Client profile with anonymization support and PII encryption."""

    __tablename__ = "clients"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id"), nullable=False, index=True
    )
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    # PII fields -- stored encrypted in database
    full_name: Mapped[str | None] = mapped_column(String(500))
    email: Mapped[str | None] = mapped_column(String(500))
    phone: Mapped[str | None] = mapped_column(String(500))
    address: Mapped[str | None] = mapped_column(Text)
    pii_consent: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    notes: Mapped[str | None] = mapped_column(Text)
    budget_tier: Mapped[str | None] = mapped_column(String(50))
    has_wearable: Mapped[bool] = mapped_column(Boolean, default=False)
    wearable_type: Mapped[str | None] = mapped_column(String(100))
    financial_audit_consent: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    sessions = relationship("AuditSession", back_populates="client", lazy="selectin")


def _encrypt_pii_fields(mapper, connection, target):
    """Encrypt PII fields before INSERT or UPDATE."""
    from app.core.encryption import encrypt_pii

    for field in PII_FIELDS:
        value = getattr(target, field)
        if value is not None and not _looks_encrypted(value):
            setattr(target, field, encrypt_pii(value))


def _decrypt_pii_fields(target, context):
    """Decrypt PII fields after loading from database."""
    from app.core.encryption import decrypt_pii

    for field in PII_FIELDS:
        value = getattr(target, field)
        if value is not None and _looks_encrypted(value):
            try:
                setattr(target, field, decrypt_pii(value))
            except Exception:
                # If decryption fails, leave the raw value
                pass


def _looks_encrypted(value: str) -> bool:
    """Check if a value appears to be base64-encoded encrypted data.

    Encrypted values are URL-safe base64 with minimum length (12 byte nonce + ciphertext + tag).
    """
    if len(value) < 40:
        return False
    try:
        import base64
        raw = base64.urlsafe_b64decode(value)
        return len(raw) >= 28  # 12 nonce + 16 tag minimum
    except Exception:
        return False


# Register SQLAlchemy events for transparent encryption
event.listen(Client, "before_insert", _encrypt_pii_fields)
event.listen(Client, "before_update", _encrypt_pii_fields)
event.listen(Client, "load", _decrypt_pii_fields)
