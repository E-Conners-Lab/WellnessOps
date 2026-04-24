"""
Audit session model.
Tracks individual audit engagements linked to a client.
Status flow: in_progress -> observations_complete -> diagnosis_pending -> report_draft -> report_final -> closed
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models.base import Base, TimestampMixin, UUIDMixin

VALID_STATUSES = (
    "in_progress",
    "observations_complete",
    "diagnosis_pending",
    "report_draft",
    "report_final",
    "closed",
)

STATUS_TRANSITIONS = {
    "in_progress": "observations_complete",
    "observations_complete": "diagnosis_pending",
    "diagnosis_pending": "report_draft",
    "report_draft": "report_final",
    "report_final": "closed",
}


class AuditSession(Base, UUIDMixin, TimestampMixin):
    """Individual audit engagement linked to a client."""

    __tablename__ = "audit_sessions"

    client_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("clients.id"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id"), nullable=False
    )
    audit_tier: Mapped[str] = mapped_column(
        String(20), nullable=False, default="core"
    )
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="in_progress", index=True
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    notes: Mapped[str | None] = mapped_column(Text)

    client = relationship("Client", back_populates="sessions", lazy="selectin")
    observations = relationship(
        "Observation", back_populates="session", lazy="selectin",
        order_by="Observation.sort_order",
    )
