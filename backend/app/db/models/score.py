"""
Category score model.
Per-category scoring for audit sessions. Supportsthe practitioner override.
"""

import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import Base, TimestampMixin, UUIDMixin

# Score label mapping
SCORE_LABELS = {
    10: "Exceptional",
    9: "Strong",
    8: "Strong",
    7: "Adequate",
    6: "Adequate",
    5: "Problematic",
    4: "Problematic",
    3: "Significant issue",
    2: "Significant issue",
    1: "Critical",
}

# Overall score labels
OVERALL_LABELS = [
    (90, "Thriving"),
    (75, "Intentional"),
    (60, "Developing"),
    (45, "Misaligned"),
    (0, "Survival Mode"),
]

# Category definitions
CORE_CATEGORIES = [
    ("setup_vs_goals", "Setup vs. Goals", False),
    ("intention", "Intention in Space and Habits", False),
    ("hidden_spaces", "The Hidden Spaces", False),
    ("kitchen_flow", "Kitchen Flow and Food System", False),
    ("natural_elements", "Natural Elements and Biophilic Design", False),
    ("sleep_environment", "Sleep Environment", False),
    ("movement", "Movement Integration", False),
    ("sensory", "Sensory Environment", False),
    ("financial_alignment", "Financial Alignment", False),
    ("wearable_data", "Wearable Data vs. Environment", False),
]

EXTENDED_CATEGORIES = [
    ("ergonomics", "Ergonomics and Physical Setup", True),
    ("art_aesthetic", "Art and Aesthetic Environment", True),
    ("library_learning", "Library and Learning Environment", True),
    ("vehicle", "Vehicle Environment", True),
    ("workspace", "Workspace Assessment", True),
]


def get_score_label(score: int) -> str:
    return SCORE_LABELS.get(score, "Unknown")


def get_overall_label(score: int) -> str:
    for threshold, label in OVERALL_LABELS:
        if score >= threshold:
            return label
    return "Survival Mode"


class CategoryScore(Base, UUIDMixin, TimestampMixin):
    """Per-category score for an audit session."""

    __tablename__ = "category_scores"
    __table_args__ = (
        UniqueConstraint("session_id", "category_key", name="uq_session_category"),
    )

    session_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("audit_sessions.id"), nullable=False, index=True
    )
    category_key: Mapped[str] = mapped_column(String(100), nullable=False)
    category_name: Mapped[str] = mapped_column(String(255), nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    ai_generated_score: Mapped[int | None] = mapped_column(Integer)
    status_label: Mapped[str] = mapped_column(String(50), nullable=False)
    what_observed: Mapped[str | None] = mapped_column(Text)
    why_it_matters: Mapped[str | None] = mapped_column(Text)
    how_to_close_gap: Mapped[str | None] = mapped_column(Text)
    is_extended_category: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    practitioner_override: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    override_notes: Mapped[str | None] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
