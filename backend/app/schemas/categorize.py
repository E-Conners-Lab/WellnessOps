"""
Categorization request and response schemas for free-form observations.
Supports multi-observation splitting.
"""

from pydantic import BaseModel, Field


class CategorizeRequest(BaseModel):
    """Request to categorize a free-form observation."""

    text: str = Field(min_length=1, max_length=5000)


class CategorizeItem(BaseModel):
    """Single categorization result. Multiple returned when input spans rooms."""

    room_area: str | None = None
    category: str | None = None
    domain_tags: list[str] = []
    confidence: float = 0.0
    text: str = ""
    clarifying_question: str | None = None
