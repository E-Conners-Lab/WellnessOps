"""
Pattern recognition service (Phase 5).
Extracts anonymized patterns from completed audits and stores them in
ChromaDB Domain 4 (Client Patterns). Queries past patterns during new
audit scoring to surface "similar clients" insights.
"""

import uuid as uuid_mod
from datetime import datetime, timezone

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.audit import AuditSession
from app.db.models.observation import Observation
from app.db.models.score import CategoryScore
from app.services.chromadb_client import get_collection
from app.services.embedding import get_embeddings, get_query_embedding
from app.services.llm import chat_completion_json

logger = structlog.stdlib.get_logger()

EXTRACTION_SYSTEM_PROMPT = """You are a pattern analyst for a wellness audit platform. Given a completed audit's category scores and observations, extract reusable patterns that could help diagnose future clients.

For each pattern you identify, provide:
- pattern_type: one of "root_cause", "correlation", "common_gap", "success_pattern"
- category_key: which scoring category this relates to
- description: 1-2 sentence anonymized pattern description (NO client names, addresses, or identifying info)
- symptom_tags: observable symptoms that indicate this pattern
- cause_tags: underlying causes or contributing factors
- frequency_hint: "common", "occasional", or "rare" based on your assessment

Return a JSON array of patterns. Aim for 3-7 patterns per audit. Focus on non-obvious connections between observations.

Respond with valid JSON only. No markdown."""

MATCH_SYSTEM_PROMPT = """You are analyzing pattern matches for a wellness audit. Given current observations and similar patterns from past audits, provide a brief insight for each relevant match.

For each pattern, explain in 1-2 sentences:
- How it connects to the current client's situation
- What the root cause turned out to be in past cases
- What to watch for

Return a JSON array:
[{{"pattern_id": "...", "relevance": 0.0-1.0, "insight": "..."}}]

Respond with valid JSON only."""


async def extract_patterns(
    db: AsyncSession,
    session_id: uuid_mod.UUID,
) -> int:
    """Extract anonymized patterns from a completed audit and store in ChromaDB.

    Returns the number of patterns stored.
    """
    # Get scores
    scores_result = await db.execute(
        select(CategoryScore)
        .where(CategoryScore.session_id == session_id)
        .order_by(CategoryScore.sort_order)
    )
    scores = scores_result.scalars().all()

    if not scores:
        logger.warning("no_scores_for_pattern_extraction", session_id=str(session_id))
        return 0

    # Get observations
    obs_result = await db.execute(
        select(Observation)
        .where(Observation.session_id == session_id, Observation.skipped.is_(False))
    )
    observations = obs_result.scalars().all()

    # Build context for LLM
    score_summary = "\n".join(
        f"- {s.category_name}: {s.score}/10 -- {s.what_observed or 'No details'}"
        for s in scores
    )
    obs_summary = "\n".join(
        f"- [{o.room_area}] {o.content}"
        for o in observations
        if o.content
    )[:3000]  # Cap context size

    user_message = f"""Audit scores:
{score_summary}

Key observations:
{obs_summary}

Extract anonymized patterns from this audit."""

    try:
        patterns = await chat_completion_json(
            system=EXTRACTION_SYSTEM_PROMPT,
            user_message=user_message,
            max_tokens=800,
            model_tier="reasoning",
        )
    except Exception:
        logger.exception("pattern_extraction_llm_failed", session_id=str(session_id))
        return 0

    # Normalize if single object returned
    if isinstance(patterns, dict):
        patterns = [patterns]

    if not patterns:
        return 0

    # Store patterns in ChromaDB Domain 4
    collection = get_collection("patterns")
    pattern_texts = []
    pattern_ids = []
    pattern_metadatas = []

    for i, p in enumerate(patterns):
        pattern_id = f"pattern_{session_id}_{i}"
        description = p.get("description", "")
        if not description:
            continue

        pattern_texts.append(description)
        pattern_ids.append(pattern_id)
        pattern_metadatas.append({
            "pattern_type": p.get("pattern_type", "unknown"),
            "category_key": p.get("category_key", ""),
            "symptom_tags": ",".join(p.get("symptom_tags", [])),
            "cause_tags": ",".join(p.get("cause_tags", [])),
            "frequency": p.get("frequency_hint", "occasional"),
            "source_session": str(session_id),
            "extracted_at": datetime.now(timezone.utc).isoformat(),
        })

    if not pattern_texts:
        return 0

    embeddings = get_embeddings(pattern_texts)
    collection.add(
        ids=pattern_ids,
        documents=pattern_texts,
        embeddings=embeddings,
        metadatas=pattern_metadatas,
    )

    logger.info(
        "patterns_extracted",
        session_id=str(session_id),
        count=len(pattern_texts),
    )

    return len(pattern_texts)


def find_similar_patterns(
    category_key: str,
    observations_text: str,
    top_k: int = 5,
) -> list[dict]:
    """Query Domain 4 for patterns similar to the given observations.

    Returns a list of pattern matches with text, metadata, and distance.
    """
    try:
        collection = get_collection("patterns")
        if collection.count() == 0:
            return []

        query_embedding = get_query_embedding(
            f"{category_key} {observations_text}"
        )

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, collection.count()),
            where={"category_key": category_key} if category_key else None,
            include=["documents", "metadatas", "distances"],
        )

        matches = []
        ids = results.get("ids", [[]])[0]
        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        dists = results.get("distances", [[]])[0]

        for i, pid in enumerate(ids):
            matches.append({
                "pattern_id": pid,
                "text": docs[i] if i < len(docs) else "",
                "metadata": metas[i] if i < len(metas) else {},
                "distance": dists[i] if i < len(dists) else 1.0,
            })

        return matches

    except Exception:
        logger.exception("pattern_search_failed", category=category_key)
        return []


async def get_pattern_insights(
    observations_text: str,
    pattern_matches: list[dict],
) -> list[dict]:
    """Use LLM to generate insights from pattern matches.

    Returns enhanced pattern matches with relevance scores and insights.
    """
    if not pattern_matches:
        return []

    patterns_context = "\n".join(
        f"- [{m['pattern_id']}] {m['text']} (type: {m['metadata'].get('pattern_type', 'unknown')})"
        for m in pattern_matches
    )

    try:
        insights = await chat_completion_json(
            system=MATCH_SYSTEM_PROMPT,
            user_message=f"""Current observations:
{observations_text}

Similar patterns from past audits:
{patterns_context}

Analyze relevance and provide insights.""",
            max_tokens=400,
            model_tier="fast",
        )

        if isinstance(insights, dict):
            insights = [insights]

        # Merge insights with pattern data
        insight_map = {i.get("pattern_id", ""): i for i in insights}
        enriched = []
        for match in pattern_matches:
            insight = insight_map.get(match["pattern_id"], {})
            enriched.append({
                **match,
                "relevance": insight.get("relevance", 0.5),
                "insight": insight.get("insight", ""),
            })

        return sorted(enriched, key=lambda x: x.get("relevance", 0), reverse=True)

    except Exception:
        logger.exception("pattern_insight_generation_failed")
        # Return matches without insights
        return [
            {**m, "relevance": 0.5, "insight": ""}
            for m in pattern_matches
        ]
