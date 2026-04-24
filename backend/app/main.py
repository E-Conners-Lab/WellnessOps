"""
WellnessOps — FastAPI Application Entry Point

RAG-powered wellness audit platform.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import structlog

from app.core.config import settings
from app.core.logging import setup_logging
from app.core.middleware import (
    CorrelationIDMiddleware,
    ExceptionHandlerMiddleware,
    HTTPSRedirectMiddleware,
    SecurityHeadersMiddleware,
)
from app.core.csrf import CSRFMiddleware
from app.core.rate_limit import RateLimitMiddleware
from app.db.database import engine
from app.api.routes import auth, clients, audits, observations, knowledge, reports, health, products, partners

logger = structlog.stdlib.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    setup_logging()
    logger.info("starting_up", environment=settings.environment)

    # Initialize ChromaDB collections
    try:
        from app.services.chromadb_client import init_collections

        init_collections()
        logger.info("chromadb_collections_initialized")
    except Exception:
        logger.exception("chromadb_init_failed")

    # Pre-load embedding model (first call will be slow otherwise)
    try:
        from app.services.embedding import load_embedding_model

        load_embedding_model()
    except Exception:
        logger.exception("embedding_model_load_failed")

    yield
    await engine.dispose()
    logger.info("shutdown_complete")


app = FastAPI(
    title="WellnessOps API",
    description="RAG-powered wellness audit platform for the wellness practitioner",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/api/docs" if settings.debug else None,
    redoc_url="/api/redoc" if settings.debug else None,
)

# CORS — restrict in production (SEC-08, SEC-09)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Middleware stack (outermost first)
# Order matters: correlation ID wraps everything, then exception handler, then security headers, then rate limit
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(CSRFMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(HTTPSRedirectMiddleware)
app.add_middleware(ExceptionHandlerMiddleware)
app.add_middleware(CorrelationIDMiddleware)

# Route registration
app.include_router(health.router, prefix="/api/v1/health", tags=["health"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(clients.router, prefix="/api/v1/clients", tags=["clients"])
app.include_router(audits.router, prefix="/api/v1/audits", tags=["audits"])
app.include_router(observations.router, prefix="/api/v1", tags=["observations"])
app.include_router(knowledge.router, prefix="/api/v1/knowledge", tags=["knowledge"])
app.include_router(reports.router, prefix="/api/v1", tags=["reports"])
app.include_router(products.router, prefix="/api/v1/products", tags=["products"])
app.include_router(partners.router, prefix="/api/v1/partners", tags=["partners"])
