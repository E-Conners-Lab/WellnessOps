"""
Document ingestion pipeline.
Upload -> extract text -> chunk -> embed -> store in ChromaDB -> update Postgres.
"""

import uuid
from datetime import datetime, timezone

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.models.knowledge import KnowledgeDocument
from app.services.chromadb_client import DOMAIN_TO_COLLECTION, get_collection
from app.services.embedding import get_embeddings
from app.utils.text_processing import chunk_text, extract_text_from_bytes

logger = structlog.stdlib.get_logger()


async def ingest_document(
    db: AsyncSession,
    *,
    domain: str,
    title: str,
    content: bytes,
    file_type: str,
    source: str | None = None,
    file_path: str | None = None,
    tags: list[str] | None = None,
    notes: str | None = None,
) -> KnowledgeDocument:
    """Run the full ingestion pipeline for a single document.

    1. Extract text from file content
    2. Chunk into overlapping segments
    3. Generate embeddings
    4. Store chunks + embeddings in ChromaDB
    5. Create/update metadata in Postgres
    """
    collection_name = DOMAIN_TO_COLLECTION.get(domain)
    if collection_name is None:
        raise ValueError(f"Unknown domain: {domain}")

    # Create Postgres record first (status: processing)
    doc = KnowledgeDocument(
        domain=domain,
        title=title,
        source=source,
        file_path=file_path,
        file_type=file_type,
        tags=tags or [],
        chromadb_collection=collection_name,
        ingestion_status="processing",
    )
    db.add(doc)
    await db.flush()

    doc_id = str(doc.id)

    try:
        # Step 1: Extract text
        text = extract_text_from_bytes(content, file_type)
        if not text.strip():
            doc.ingestion_status = "failed"
            doc.notes = "No text content extracted"
            await db.flush()
            raise ValueError("No text content could be extracted from the document")

        logger.info("text_extracted", doc_id=doc_id, length=len(text))

        # Step 2: Chunk
        chunks = chunk_text(
            text,
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )
        logger.info("text_chunked", doc_id=doc_id, chunk_count=len(chunks))

        # Step 3: Generate embeddings
        embeddings = get_embeddings(chunks)
        logger.info("embeddings_generated", doc_id=doc_id)

        # Step 4: Store in ChromaDB
        collection = get_collection(domain)
        chunk_ids = [f"{doc_id}_chunk_{i}" for i in range(len(chunks))]
        metadatas = [
            {
                "document_id": doc_id,
                "title": title,
                "domain": domain,
                "chunk_index": i,
                "source": source or "",
                **({"tags": ",".join(tags)} if tags else {}),
            }
            for i in range(len(chunks))
        ]

        collection.add(
            ids=chunk_ids,
            documents=chunks,
            embeddings=embeddings,
            metadatas=metadatas,
        )
        logger.info("chunks_stored_in_chromadb", doc_id=doc_id, count=len(chunks))

        # Step 5: Update Postgres metadata
        doc.chunk_count = len(chunks)
        doc.ingestion_status = "completed"
        doc.ingested_at = datetime.now(timezone.utc)
        if notes:
            doc.notes = notes
        await db.flush()

        logger.info("ingestion_complete", doc_id=doc_id, domain=domain)
        return doc

    except Exception as exc:
        doc.ingestion_status = "failed"
        doc.notes = str(exc)[:500]
        await db.flush()
        logger.exception("ingestion_failed", doc_id=doc_id)
        raise


async def delete_document_chunks(doc: KnowledgeDocument) -> None:
    """Remove all chunks for a document from ChromaDB."""
    try:
        collection = get_collection(doc.domain)
        # ChromaDB where filter to find all chunks for this document
        collection.delete(where={"document_id": str(doc.id)})
        logger.info("chunks_deleted", doc_id=str(doc.id), domain=doc.domain)
    except Exception:
        logger.exception("chunk_deletion_failed", doc_id=str(doc.id))
        raise
