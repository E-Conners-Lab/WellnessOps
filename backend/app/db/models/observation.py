"""
Observation model.
Individual data points within an audit session.
Supports text, photos, measurements, and wearable data.
"""

import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, JSON, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models.base import Base, TimestampMixin, UUIDMixin


class Observation(Base, UUIDMixin, TimestampMixin):
    """Single observation within an audit session."""

    __tablename__ = "observations"

    session_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("audit_sessions.id"), nullable=False, index=True
    )
    room_area: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    category: Mapped[str | None] = mapped_column(String(100))
    observation_type: Mapped[str] = mapped_column(String(30), nullable=False, default="text")
    content: Mapped[str | None] = mapped_column(Text)
    photo_path: Mapped[str | None] = mapped_column(String(500))
    photo_thumbnail_path: Mapped[str | None] = mapped_column(String(500))
    is_from_structured_flow: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )
    auto_categorized: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    domain_tags: Mapped[list[str] | None] = mapped_column(JSON)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    prompt_key: Mapped[str | None] = mapped_column(String(100))
    skipped: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    session = relationship("AuditSession", back_populates="observations")
