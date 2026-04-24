"""
Report model with versioning.
Generated reports linked to audit sessions.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import Base, TimestampMixin, UUIDMixin


class Report(Base, UUIDMixin, TimestampMixin):
    """Generated audit report with versioning."""

    __tablename__ = "reports"
    __table_args__ = (
        UniqueConstraint("session_id", "version", name="uq_session_version"),
    )

    session_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("audit_sessions.id"), nullable=False, index=True
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="draft")
    overall_score: Mapped[int] = mapped_column(Integer, nullable=False)
    overall_label: Mapped[str] = mapped_column(String(50), nullable=False)
    priority_action_plan: Mapped[dict | None] = mapped_column(JSON)
    vision_section: Mapped[str | None] = mapped_column(Text)
    next_steps: Mapped[str | None] = mapped_column(Text)
    pdf_path: Mapped[str | None] = mapped_column(String(500))
    generated_by: Mapped[str] = mapped_column(String(50), nullable=False, default="system")
    approved_by: Mapped[uuid.UUID | None] = mapped_column(Uuid)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
