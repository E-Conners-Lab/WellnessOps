"""
Hybrid RAG search pipeline.
ChromaDB semantic similarity + BM25 keyword ranking, fused via reciprocal rank fusion.
Returns top-K results across specified domains.
"""

import structlog
from rank_bm25 import BM25Okapi

from app.core.config import settings
from app.services.chromadb_client import DOMAIN_COLLECTIONS, get_collection_by_name
from app.services.embedding import get_query_embedding

logger = structlog.stdlib.get_logger()


def reciprocal_rank_fusion(
    ranked_lists: list[list[str]],
    k: int = 60,
) -> list[str]:
    """Merge multiple ranked lists using reciprocal rank fusion.

    Each item's score is sum of 1/(k + rank) across all lists it appears in.
    Returns items sorted by fused score, highest first.
    """
    scores: dict[str, float] = {}
    for ranked_list in ranked_lists:
        for rank, item_id in enumerate(ranked_list):
            scores[item_id] = scores.get(item_id, 0.0) + 1.0 / (k + rank + 1)

    return sorted(scores.keys(), key=lambda x: scores[x], reverse=True)


def hybrid_search(
    query: str,
    domains: list[str] | None = None,
    top_k: int | None = None,
) -> list[dict]:
    """Run hybrid search across specified ChromaDB domains.

    1. Semantic search via ChromaDB (cosine similarity on embeddings)
    2. Keyword search via BM25 on stored documents
    3. Reciprocal rank fusion to merge results
    4. Return top-K with text and metadata

    Args:
        query: The search query string.
        domains: List of domain collection names to search. None means all domains.
        top_k: Number of results to return. Defaults to settings.rag_top_k.
    """
    if top_k is None:
        top_k = settings.rag_top_k

    if domains is None:
        domains = list(DOMAIN_COLLECTIONS.keys())

    query_embedding = get_query_embedding(query)
    all_semantic_ids: list[str] = []
    all_bm25_ids: list[str] = []
    doc_map: dict[str, dict] = {}

    for domain_name in domains:
        try:
            collection = get_collection_by_name(domain_name)
            count = collection.count()
            if count == 0:
                continue

            # Semantic search
            n_results = min(top_k * 2, count)
            semantic_results = collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                include=["documents", "metadatas", "distances"],
            )

            ids = semantic_results["ids"][0] if semantic_results["ids"] else []
            docs = (
                semantic_results["documents"][0]
                if semantic_results["documents"]
                else []
            )
            metas = (
                semantic_results["metadatas"][0]
                if semantic_results["metadatas"]
                else []
            )
            distances = (
                semantic_results["distances"][0]
                if semantic_results["distances"]
                else []
            )

            all_semantic_ids.extend(ids)

            for i, chunk_id in enumerate(ids):
                doc_map[chunk_id] = {
                    "id": chunk_id,
                    "text": docs[i] if i < len(docs) else "",
                    "metadata": metas[i] if i < len(metas) else {},
                    "distance": distances[i] if i < len(distances) else 1.0,
                    "domain": domain_name,
                }

            # BM25 keyword search on the same documents
            if docs:
                tokenized_docs = [doc.lower().split() for doc in docs]
                bm25 = BM25Okapi(tokenized_docs)
                bm25_scores = bm25.get_scores(query.lower().split())

                scored_pairs = sorted(
                    zip(ids, bm25_scores), key=lambda x: x[1], reverse=True
                )
                bm25_ranked = [pair[0] for pair in scored_pairs]
                all_bm25_ids.extend(bm25_ranked)

        except Exception:
            logger.exception("search_domain_failed", domain=domain_name)
            continue

    if not doc_map:
        return []

    # Reciprocal rank fusion
    fused_ids = reciprocal_rank_fusion([all_semantic_ids, all_bm25_ids])

    # Return top-K results
    results = []
    for chunk_id in fused_ids[:top_k]:
        if chunk_id in doc_map:
            results.append(doc_map[chunk_id])

    logger.info(
        "hybrid_search_complete",
        query_length=len(query),
        domains_searched=len(domains),
        results_returned=len(results),
    )

    return results
