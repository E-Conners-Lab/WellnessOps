"""
Knowledge base management routes.
Document ingestion, domain stats, retrieval testing.
Auth required (SEC-02).
"""

from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.database import get_db
from app.db.models.knowledge import KnowledgeDocument
from app.db.models.user import User
from app.schemas.common import APIResponse
from app.schemas.knowledge import (
    DomainStats,
    KnowledgeDocumentResponse,
    SearchRequest,
    SearchResult,
)
from app.services.audit_logger import write_audit_log
from app.services.chromadb_client import DOMAIN_COLLECTIONS, DOMAIN_TO_COLLECTION
from app.services.file_handler import FileValidationError, validate_file
from app.services.ingestion import delete_document_chunks, ingest_document
from app.services.rag import hybrid_search

logger = structlog.stdlib.get_logger()
router = APIRouter()


@router.get("/documents")
async def list_documents(
    domain: str | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    """List all ingested documents with optional domain filter."""
    query = select(KnowledgeDocument).order_by(KnowledgeDocument.created_at.desc())
    if domain:
        query = query.where(KnowledgeDocument.domain == domain)

    result = await db.execute(query)
    docs = result.scalars().all()

    return APIResponse(
        data=[KnowledgeDocumentResponse.model_validate(d).model_dump() for d in docs]
    )


@router.post("/documents")
async def upload_and_ingest(
    request: Request,
    file: UploadFile = File(...),
    domain: str = Form(...),
    title: str = Form(...),
    source: str = Form(default=None),
    tags: str = Form(default=""),
    notes: str = Form(default=None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    """Upload and ingest a document into the knowledge base."""
    # Validate domain
    if domain not in DOMAIN_TO_COLLECTION:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid domain: {domain}. Must be one of: {list(DOMAIN_TO_COLLECTION.keys())}",
        )

    # Read and validate file
    content = await file.read()
    try:
        validated_type = validate_file(
            content, file.filename or "unknown", file.content_type or ""
        )
    except FileValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    # Parse tags (comma-separated string)
    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []

    # Run ingestion pipeline
    try:
        doc = await ingest_document(
            db,
            domain=domain,
            title=title,
            content=content,
            file_type=validated_type,
            source=source,
            tags=tag_list,
            notes=notes,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    await write_audit_log(
        db,
        action="knowledge_document_ingested",
        user_id=user.id,
        resource_type="knowledge_document",
        resource_id=doc.id,
        details={"domain": domain, "title": title},
        request=request,
    )

    return APIResponse(
        data=KnowledgeDocumentResponse.model_validate(doc).model_dump()
    )


@router.get("/documents/{document_id}")
async def get_document(
    document_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    """Get document metadata and preview of stored chunks."""
    result = await db.execute(
        select(KnowledgeDocument).where(KnowledgeDocument.id == document_id)
    )
    doc = result.scalar_one_or_none()
    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    doc_data = KnowledgeDocumentResponse.model_validate(doc).model_dump()

    # Fetch a few chunk previews from ChromaDB
    try:
        from app.services.chromadb_client import get_collection

        collection = get_collection(doc.domain)
        preview = collection.get(
            where={"document_id": str(doc.id)},
            limit=3,
            include=["documents"],
        )
        doc_data["chunk_preview"] = preview.get("documents", [])[:3]
    except Exception:
        doc_data["chunk_preview"] = []

    return APIResponse(data=doc_data)


@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: UUID,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    """Remove document metadata from Postgres and chunks from ChromaDB."""
    result = await db.execute(
        select(KnowledgeDocument).where(KnowledgeDocument.id == document_id)
    )
    doc = result.scalar_one_or_none()
    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    # Delete chunks from ChromaDB
    await delete_document_chunks(doc)

    # Delete from Postgres
    await db.delete(doc)

    await write_audit_log(
        db,
        action="knowledge_document_deleted",
        user_id=user.id,
        resource_type="knowledge_document",
        resource_id=doc.id,
        details={"domain": doc.domain, "title": doc.title},
        request=request,
    )

    return APIResponse(data={"message": "Document deleted"})


@router.get("/domains")
async def list_domain_stats(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    """List domain stats: doc count, chunk count per domain."""
    # Query Postgres for document and chunk counts per domain
    result = await db.execute(
        select(
            KnowledgeDocument.domain,
            func.count(KnowledgeDocument.id).label("doc_count"),
            func.coalesce(func.sum(KnowledgeDocument.chunk_count), 0).label(
                "chunk_count"
            ),
        )
        .where(KnowledgeDocument.ingestion_status == "completed")
        .group_by(KnowledgeDocument.domain)
    )
    db_stats = {row.domain: (row.doc_count, row.chunk_count) for row in result}

    stats = []
    for domain_key, collection_name in DOMAIN_TO_COLLECTION.items():
        doc_count, chunk_count = db_stats.get(domain_key, (0, 0))
        stats.append(
            DomainStats(
                domain=domain_key,
                collection_name=collection_name,
                description=DOMAIN_COLLECTIONS[collection_name]["description"],
                document_count=doc_count,
                total_chunks=chunk_count,
            ).model_dump()
        )

    return APIResponse(data=stats)


@router.post("/search")
async def search_knowledge(
    body: SearchRequest,
    user: User = Depends(get_current_user),
) -> APIResponse:
    """Search across knowledge domains using hybrid RAG."""
    # Map domain keys to collection names if provided
    domain_collections = None
    if body.domains:
        domain_collections = []
        for d in body.domains:
            coll = DOMAIN_TO_COLLECTION.get(d)
            if coll is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid domain: {d}",
                )
            domain_collections.append(coll)

    results = hybrid_search(
        query=body.query,
        domains=domain_collections,
        top_k=body.top_k,
    )

    return APIResponse(
        data=[SearchResult(**r).model_dump() for r in results]
    )
