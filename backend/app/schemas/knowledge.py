"""
Knowledge base request and response schemas.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class KnowledgeDocumentResponse(BaseModel):
    """Knowledge document metadata returned from API."""

    id: uuid.UUID
    domain: str
    title: str
    source: str | None = None
    file_type: str | None = None
    tags: list[str] = []
    chunk_count: int = 0
    chromadb_collection: str
    ingested_at: datetime | None = None
    ingestion_status: str
    notes: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class DomainStats(BaseModel):
    """Stats for a single knowledge domain."""

    domain: str
    collection_name: str
    description: str
    document_count: int = 0
    total_chunks: int = 0


class SearchRequest(BaseModel):
    """Knowledge base search request."""

    query: str = Field(min_length=1, max_length=1000)
    domains: list[str] | None = None
    top_k: int = Field(default=10, ge=1, le=50)


class SearchResult(BaseModel):
    """A single search result chunk."""

    id: str
    text: str
    metadata: dict = {}
    distance: float | None = None
    domain: str
