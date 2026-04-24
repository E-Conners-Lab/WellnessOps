"""
Embedding model management.
Uses BAAI/bge-large-en-v1.5 via sentence-transformers.
Model loaded once at startup and shared across requests.
"""

import structlog

from app.core.config import settings

logger = structlog.stdlib.get_logger()

_model = None


def load_embedding_model() -> None:
    """Load the embedding model into memory. Called once at app startup."""
    global _model
    if _model is not None:
        return

    from sentence_transformers import SentenceTransformer

    logger.info("loading_embedding_model", model=settings.embedding_model)
    _model = SentenceTransformer(settings.embedding_model)
    logger.info("embedding_model_loaded", model=settings.embedding_model)


def get_embeddings(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for a list of texts.

    Returns a list of embedding vectors.
    """
    if _model is None:
        load_embedding_model()

    embeddings = _model.encode(texts, normalize_embeddings=True)
    return embeddings.tolist()


def get_query_embedding(query: str) -> list[float]:
    """Generate an embedding for a single query string."""
    if _model is None:
        load_embedding_model()

    embedding = _model.encode(query, normalize_embeddings=True)
    return embedding.tolist()
