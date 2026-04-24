"""
ChromaDB client singleton and domain collection management.
7 knowledge domain collections initialized at app startup.
"""

import structlog
import chromadb

from app.core.config import settings

logger = structlog.stdlib.get_logger()

# Domain collection definitions with their metadata schemas
DOMAIN_COLLECTIONS = {
    "domain_well": {
        "description": "WELL Building Standard",
        "metadata_fields": ["concept", "section", "threshold_type"],
    },
    "domain_research": {
        "description": "Articles & Research",
        "metadata_fields": ["topic_tags", "source", "publish_date", "study_type"],
    },
    "domain_products": {
        "description": "Product Recommendations",
        "metadata_fields": ["category", "price_range", "is_recommended"],
    },
    "domain_patterns": {
        "description": "Client Patterns",
        "metadata_fields": [
            "pattern_type",
            "symptom_tags",
            "cause_tags",
            "frequency",
        ],
    },
    "domain_philosophies": {
        "description": "Lifestyle Philosophies",
        "metadata_fields": ["philosophy", "principle"],
    },
    "domain_aesthetics": {
        "description": "Art & Aesthetics",
        "metadata_fields": ["topic", "medium"],
    },
    "domain_partners": {
        "description": "Partners & Vendors",
        "metadata_fields": ["category", "location", "pricing_tier"],
    },
}

# Map user-facing domain names to collection names
DOMAIN_TO_COLLECTION = {
    "well": "domain_well",
    "research": "domain_research",
    "products": "domain_products",
    "patterns": "domain_patterns",
    "philosophies": "domain_philosophies",
    "aesthetics": "domain_aesthetics",
    "partners": "domain_partners",
}

_client = None


def get_chroma_client():
    """Get or create the ChromaDB HTTP client singleton."""
    global _client
    if _client is None:
        _client = chromadb.HttpClient(
            host=settings.chroma_host,
            port=settings.chroma_port,
        )
        logger.info(
            "chromadb_client_created",
            host=settings.chroma_host,
            port=settings.chroma_port,
        )
    return _client


def init_collections() -> None:
    """Create all 7 domain collections if they do not exist."""
    client = get_chroma_client()
    for name, meta in DOMAIN_COLLECTIONS.items():
        client.get_or_create_collection(
            name=name,
            metadata={"description": meta["description"]},
        )
        logger.info("chromadb_collection_ready", collection=name)


def get_collection(domain: str) -> chromadb.Collection:
    """Get a ChromaDB collection by domain name."""
    collection_name = DOMAIN_TO_COLLECTION.get(domain)
    if collection_name is None:
        raise ValueError(f"Unknown domain: {domain}")
    client = get_chroma_client()
    return client.get_collection(name=collection_name)


def get_collection_by_name(collection_name: str) -> chromadb.Collection:
    """Get a ChromaDB collection by its internal name."""
    client = get_chroma_client()
    return client.get_collection(name=collection_name)
