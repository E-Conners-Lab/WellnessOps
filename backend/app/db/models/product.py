"""
Product model. Vetted product catalog for recommendations.
"""

from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import Base, TimestampMixin, UUIDMixin


class Product(Base, UUIDMixin, TimestampMixin):
    """Vetted product recommendation."""

    __tablename__ = "products"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    brand: Mapped[str | None] = mapped_column(String(255))
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    price_range: Mapped[str | None] = mapped_column(String(50))
    purchase_link: Mapped[str | None] = mapped_column(Text)
    why_recommended: Mapped[str] = mapped_column(Text, nullable=False)
    best_for: Mapped[str | None] = mapped_column(Text)
    contraindications: Mapped[str | None] = mapped_column(Text)
    practitioner_note: Mapped[str | None] = mapped_column(Text)
    is_recommended: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    not_recommended_reason: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
