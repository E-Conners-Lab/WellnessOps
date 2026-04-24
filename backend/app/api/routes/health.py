"""Health check endpoints. PUBLIC -- no auth required."""

import structlog
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db

logger = structlog.stdlib.get_logger()
router = APIRouter()


@router.get("")
async def health_check():
    """Basic service health check."""
    return {"status": "healthy", "service": "wellness-ops"}


@router.get("/db")
async def db_health(db: AsyncSession = Depends(get_db)):
    """Database connectivity check."""
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "healthy", "component": "database"}
    except Exception as exc:
        logger.error("db_health_check_failed", error=str(exc))
        return {"status": "unhealthy", "component": "database"}


@router.get("/chroma")
async def chroma_health():
    """ChromaDB connectivity check."""
    try:
        from app.services.chromadb_client import get_chroma_client

        client = get_chroma_client()
        collections = client.list_collections()
        return {
            "status": "healthy",
            "component": "chromadb",
            "collections": len(collections),
        }
    except Exception as exc:
        logger.error("chroma_health_check_failed", error=str(exc))
        return {"status": "unhealthy", "component": "chromadb"}
