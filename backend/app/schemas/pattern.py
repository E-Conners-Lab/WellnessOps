"""Pattern matching schemas."""

from pydantic import BaseModel, Field


class PatternMatchRequest(BaseModel):
    """Request to find similar patterns."""

    observations_text: str = Field(min_length=1, max_length=5000)
    category_key: str | None = None
    top_k: int = Field(default=5, ge=1, le=20)


class PatternMatch(BaseModel):
    """A single pattern match from past audits."""

    pattern_id: str
    text: str
    metadata: dict = {}
    distance: float | None = None
    relevance: float = 0.5
    insight: str = ""
