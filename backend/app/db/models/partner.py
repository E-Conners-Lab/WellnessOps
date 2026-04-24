"""
Partner model. Partner and vendor directory for referrals.
"""

from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import Base, TimestampMixin, UUIDMixin


class Partner(Base, UUIDMixin, TimestampMixin):
    """Partner or vendor for client referrals."""

    __tablename__ = "partners"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    business_name: Mapped[str | None] = mapped_column(String(255))
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    location: Mapped[str | None] = mapped_column(String(255))
    contact_email: Mapped[str | None] = mapped_column(String(255))
    contact_phone: Mapped[str | None] = mapped_column(String(50))
    website: Mapped[str | None] = mapped_column(String(500))
    why_recommended: Mapped[str] = mapped_column(Text, nullable=False)
    best_for_client_type: Mapped[str | None] = mapped_column(Text)
    pricing_tier: Mapped[str | None] = mapped_column(String(50))
    is_ambassador: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    practitioner_note: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
