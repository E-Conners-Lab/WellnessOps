"""
Score generation service.
Groups observations by category, retrieves knowledge via RAG,
sends to LLM with scoring criteria and the practitioner's voice guidelines,
parses structured scores.
"""

import uuid as uuid_mod

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.observation import Observation
from app.db.models.score import (
    CORE_CATEGORIES,
    EXTENDED_CATEGORIES,
    CategoryScore,
    get_score_label,
)
from app.services.llm import chat_completion_json
from app.services.rag import hybrid_search

logger = structlog.stdlib.get_logger()

# Maps room_area -> category_key for grouping observations
ROOM_TO_CATEGORY = {
    "entry": "setup_vs_goals",
    "living": "intention",
    "hidden_spaces": "hidden_spaces",
    "kitchen": "kitchen_flow",
    "bedroom": "sleep_environment",
    "workspace": "workspace",
    "extended": "art_aesthetic",
    "wearable": "wearable_data",
    "financial": "financial_alignment",
    "client_responses": "setup_vs_goals",
}

SCORING_SYSTEM_PROMPT = """You are the wellness practitioner's diagnostic brain. You are scoring a home wellness audit.

For the given category, you have:
1. the practitioner's field observations from the client's home
2. Relevant knowledge from the wellness knowledge base
3. The scoring criteria

Score this category on a 1-10 scale. Be specific and grounded in what was actually observed. Write in the practitioner's voice: direct, warm, specific, occasionally funny, never clinical.

Respond with valid JSON only:
{{
  "score": 1-10,
  "what_observed": "2-3 sentences about whatthe practitioner saw, specific to this client",
  "why_it_matters": "2-3 sentences connecting observations to health/wellness impact, citing knowledge when relevant",
  "how_to_close_gap": "2-3 specific, prioritized recommendations"
}}

IMPORTANT: Base the score ONLY on actual observations provided. If no observations exist for this category, score conservatively (5) and note the gap. Never fabricate observations."""

SCORING_CRITERIA = {
    "setup_vs_goals": "Does the environment match stated goals? 10=perfect alignment, 7=mostly aligned with 1-2 gaps, 4=significant disconnect, 1=complete misalignment",
    "intention": "Are things placed with purpose or by default? 10=every placement deliberate, 7=intention in main areas, 4=mostly accidental, 1=pure accumulated default",
    "hidden_spaces": "What do closets, drawers, cabinets reveal? 10=as organized as visible spaces, 7=some effort, 4=worse than visible areas, 1=unacknowledged overwhelm",
    "kitchen_flow": "Is there a food system? 10=clear system supporting actual meals, 7=good ingredients no plan, 4=reactive eating, 1=complete decision fatigue",
    "natural_elements": "Light, plants, air, nature connection? 10=strong biophilic presence, 7=some elements not integrated, 4=minimal nature, 1=complete disconnection",
    "sleep_environment": "Temp, light, sound, humidity, bed view? 10=optimized, 7=good foundation with 1-2 issues, 4=multiple disruptors, 1=actively hostile to sleep",
    "movement": "Is movement built into daily architecture? 10=woven into routines, 7=some infrastructure, 4=sedentary default, 1=discourages movement",
    "sensory": "What does the nervous system absorb all day? 10=intentionally curated, 7=some awareness, 4=mostly accidental, 1=overload or deprivation",
    "financial_alignment": "Does spending match stated priorities? 10=perfectly reflects values, 7=mostly aligned, 4=significant misalignment, 1=complete disconnect",
    "wearable_data": "Does wearable data explain the environment? 10=data confirms support, 7=mostly positive, 4=clear negative patterns, 1=significant health impact",
    "ergonomics": "Body support vs slow damage? 10=every surface supports, 7=mostly good, 4=multiple problem areas, 1=chronic strain sources",
    "art_aesthetic": "Visual intelligence of space? 10=curated with intention, 7=some thought, 4=mostly default, 1=visual chaos or emptiness",
    "library_learning": "What does the reading life communicate? 10=active engaged learner, 7=some reading presence, 4=aspirational only, 1=no learning environment",
    "vehicle": "What does the car reveal? 10=extension of intentional living, 7=maintained, 4=neglected, 1=mobile stress environment",
    "workspace": "8+ hours/day environment? 10=optimized for sustained focus, 7=functional with gaps, 4=borrowed/compromised, 1=actively harmful",
}


async def generate_scores(
    db: AsyncSession,
    session_id: str | uuid_mod.UUID,
    audit_tier: str,
) -> list[CategoryScore]:
    """Generate AI scores for all applicable categories.

    1. Collect observations grouped by category
    2. For each category, retrieve relevant knowledge via RAG
    3. Send observations + knowledge + criteria to LLM
    4. Parse and store scores
    """
    # Ensure session_id is a UUID
    if isinstance(session_id, str):
        session_id = uuid_mod.UUID(session_id)

    # Get all observations for this session
    result = await db.execute(
        select(Observation).where(Observation.session_id == session_id)
    )
    observations = result.scalars().all()

    # Group observations by category
    obs_by_category: dict[str, list[str]] = {}
    for obs in observations:
        if obs.skipped or not obs.content:
            continue
        cat_key = ROOM_TO_CATEGORY.get(obs.room_area, obs.room_area)
        obs_by_category.setdefault(cat_key, []).append(obs.content)

    # Determine which categories to score
    categories = list(CORE_CATEGORIES)
    if audit_tier == "extended":
        categories.extend(EXTENDED_CATEGORIES)

    scores: list[CategoryScore] = []
    for idx, (cat_key, cat_name, is_extended) in enumerate(categories):
        cat_observations = obs_by_category.get(cat_key, [])

        # Skip categories with no observations -- don't score what wasn't observed
        if not cat_observations:
            logger.info("category_skipped_no_observations", category=cat_key)
            continue

        obs_text = "\n".join(f"- {o}" for o in cat_observations)

        # RAG: retrieve relevant knowledge
        knowledge_context = ""
        try:
            rag_results = hybrid_search(query=f"{cat_name} wellness home audit", top_k=5)
            if rag_results:
                knowledge_chunks = [r["text"][:300] for r in rag_results[:3]]
                knowledge_context = "\n\n".join(knowledge_chunks)
        except Exception:
            logger.warning("rag_search_failed_for_scoring", category=cat_key)

        # Pattern matching: query Domain 4 for similar past patterns
        pattern_context = ""
        try:
            from app.services.pattern_matcher import find_similar_patterns

            pattern_matches = find_similar_patterns(cat_key, obs_text, top_k=3)
            if pattern_matches:
                pattern_lines = [
                    f"- {m['text']} (type: {m['metadata'].get('pattern_type', 'unknown')})"
                    for m in pattern_matches
                ]
                pattern_context = "\n".join(pattern_lines)
        except Exception:
            logger.warning("pattern_match_failed_for_scoring", category=cat_key)

        criteria = SCORING_CRITERIA.get(cat_key, "Score 1-10 based on observations.")

        user_message = f"""Category: {cat_name}
Scoring criteria: {criteria}

the practitioner's observations:
{obs_text}

{"Relevant knowledge:" + chr(10) + knowledge_context if knowledge_context else "No specific knowledge base entries for this category."}

{"Patterns from past audits:" + chr(10) + pattern_context if pattern_context else ""}

Score this category."""

        try:
            result_data = await chat_completion_json(
                system=SCORING_SYSTEM_PROMPT,
                user_message=user_message,
                max_tokens=600,
                model_tier="reasoning",
            )

            score_val = max(1, min(10, int(result_data.get("score", 5))))
            score = CategoryScore(
                session_id=session_id,
                category_key=cat_key,
                category_name=cat_name,
                score=score_val,
                ai_generated_score=score_val,
                status_label=get_score_label(score_val),
                what_observed=result_data.get("what_observed", ""),
                why_it_matters=result_data.get("why_it_matters", ""),
                how_to_close_gap=result_data.get("how_to_close_gap", ""),
                is_extended_category=is_extended,
                sort_order=idx,
            )
        except Exception:
            logger.exception("score_generation_failed", category=cat_key)
            score = CategoryScore(
                session_id=session_id,
                category_key=cat_key,
                category_name=cat_name,
                score=5,
                ai_generated_score=5,
                status_label=get_score_label(5),
                what_observed="Score generation encountered an error. Manual review recommended.",
                is_extended_category=is_extended,
                sort_order=idx,
            )

        db.add(score)
        scores.append(score)

        logger.info(
            "category_scored",
            category=cat_key,
            score=score.score,
            has_observations=len(cat_observations) > 0,
        )

    await db.flush()
    return scores
