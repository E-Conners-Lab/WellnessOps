"""
Knowledge document metadata model.
Tracks documents ingested into ChromaDB with their domain and status.
"""

from datetime import datetime

from sqlalchemy import JSON, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import Base, TimestampMixin, UUIDMixin


class KnowledgeDocument(Base, UUIDMixin, TimestampMixin):
    """Metadata for a document ingested into the ChromaDB knowledge base."""

    __tablename__ = "knowledge_documents"

    domain: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    source: Mapped[str | None] = mapped_column(String(500))
    file_path: Mapped[str | None] = mapped_column(String(500))
    file_type: Mapped[str | None] = mapped_column(String(50))
    tags: Mapped[list[str] | None] = mapped_column(JSON)
    chunk_count: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )
    chromadb_collection: Mapped[str] = mapped_column(String(100), nullable=False)
    ingested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ingestion_status: Mapped[str] = mapped_column(
        String(30), nullable=False, server_default="pending"
    )
    notes: Mapped[str | None] = mapped_column(Text)
