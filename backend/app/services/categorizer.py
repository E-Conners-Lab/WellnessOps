"""
Free-form observation categorizer (Mode 2).
Routes to Claude or Ollama via the LLM abstraction layer.
Supports multi-observation splitting: detects when a single input covers
multiple rooms and returns separate categorizations for each.
"""

import structlog

from app.services.llm import chat_completion_json

logger = structlog.stdlib.get_logger()

CONFIDENCE_THRESHOLD = 0.7

ROOM_TAXONOMY = {
    "entry": "Entry and curb appeal, first impressions, threshold intention",
    "living": "Living spaces, dominant feeling, natural light, art, biophilic elements, sensory environment, ergonomics, seating",
    "kitchen": "Kitchen, fridge contents, food system, meal planning, pantry, eating location",
    "hidden_spaces": "Hidden spaces, closets, junk drawers, under-sink areas, unseen clutter",
    "bedroom": "Bedroom, sleep environment, nightstand, light, temperature, humidity, work visibility",
    "workspace": "Workspace, dedicated vs borrowed, lighting, chair, sightline, separation from rest",
    "extended": "Extended areas, books, art, vehicle, office",
    "wearable": "Wearable data, sleep scores, HRV, stress, patterns",
    "financial": "Financial alignment, spending categories, contradictions with stated goals",
    "client_responses": "Client's own words, primary concern, what they have tried, ideal life, answer patterns",
}

DOMAIN_TAGS_OPTIONS = [
    "well", "research", "products", "patterns",
    "philosophies", "aesthetics", "partners",
]

SYSTEM_PROMPT = """You are a categorization assistant for a wellness audit platform. Given a free-form observation from a home wellness audit, determine which room areas and categories it belongs to.

IMPORTANT: The input may describe observations about MULTIPLE rooms or areas. If so, split it into separate observations, one per room area. Each split observation should contain only the text relevant to that room.

Room areas and their scope:
{taxonomy}

Knowledge domains: {domains}

Respond with a JSON array. Each element represents one observation:

[
  {{
    "room_area": "...",
    "category": "...",
    "domain_tags": ["..."],
    "confidence": 0.0-1.0,
    "text": "the portion of the original text for this observation"
  }}
]

If any part is ambiguous (confidence < 0.7), include a clarifying_question field for that element:

[
  {{
    "room_area": null,
    "category": null,
    "domain_tags": [],
    "confidence": 0.3,
    "text": "the ambiguous portion",
    "clarifying_question": "Which area does this relate to?"
  }}
]

If the entire input is about one room, return an array with one element. Always return a JSON array, never a single object. Respond with valid JSON only. No markdown."""


def _build_system_prompt() -> str:
    taxonomy_text = "\n".join(
        f"- {area}: {desc}" for area, desc in ROOM_TAXONOMY.items()
    )
    return SYSTEM_PROMPT.format(
        taxonomy=taxonomy_text,
        domains=", ".join(DOMAIN_TAGS_OPTIONS),
    )


async def categorize_text(text: str) -> list[dict]:
    """Categorize a free-form observation using the configured LLM.

    Returns a list of categorization dicts. Multiple items when the input
    covers multiple rooms.

    Each dict has keys:
    - room_area: str | None
    - category: str | None
    - domain_tags: list[str]
    - confidence: float
    - text: str (the relevant portion of the input)
    - clarifying_question: str | None
    """
    try:
        result = await chat_completion_json(
            system=_build_system_prompt(),
            user_message=f"Categorize this observation:\n\n{text}",
            max_tokens=600,
            model_tier="fast",
        )

        # Normalize: if the LLM returned a single object instead of an array, wrap it
        if isinstance(result, dict):
            result = [result]

        categorizations = []
        for item in result:
            categorizations.append({
                "room_area": item.get("room_area"),
                "category": item.get("category"),
                "domain_tags": item.get("domain_tags", []),
                "confidence": float(item.get("confidence", 0)),
                "text": item.get("text", text),
                "clarifying_question": item.get("clarifying_question"),
            })

        logger.info(
            "categorization_complete",
            observation_count=len(categorizations),
            rooms=[c["room_area"] for c in categorizations],
        )

        return categorizations

    except Exception:
        logger.exception("categorization_llm_failed")
        return _fallback_categorization(text)


def _fallback_categorization(text: str) -> list[dict]:
    """Keyword-based fallback when LLM is unavailable. Detects multiple rooms."""
    text_lower = text.lower()

    room_keywords = {
        "kitchen": ["fridge", "kitchen", "pantry", "food", "meal", "cook", "eating"],
        "bedroom": ["bed", "sleep", "nightstand", "pillow", "mattress", "blackout"],
        "living": ["living room", "couch", "sofa", "art", "plant"],
        "workspace": ["desk", "chair", "monitor", "office", "work from home"],
        "hidden_spaces": ["closet", "drawer", "cabinet", "under sink", "clutter"],
        "entry": ["entry", "front door", "curb", "porch", "threshold"],
        "wearable": ["whoop", "oura", "apple watch", "garmin", "hrv", "sleep score"],
        "financial": ["spending", "bank", "budget", "financial", "money"],
    }

    # Score each room
    room_scores: dict[str, int] = {}
    for room, keywords in room_keywords.items():
        count = sum(1 for kw in keywords if kw in text_lower)
        if count > 0:
            room_scores[room] = count

    if not room_scores:
        return [{
            "room_area": None,
            "category": None,
            "domain_tags": [],
            "confidence": 0.2,
            "text": text,
            "clarifying_question": "Which area of the home does this observation relate to?",
        }]

    # If multiple rooms detected, return one entry per room
    results = []
    for room, count in sorted(room_scores.items(), key=lambda x: x[1], reverse=True):
        confidence = min(0.3 + (count * 0.15), 0.65)
        results.append({
            "room_area": room,
            "category": None,
            "domain_tags": [],
            "confidence": confidence,
            "text": text,
            "clarifying_question": "Which area of the home does this observation relate to?" if confidence < CONFIDENCE_THRESHOLD else None,
        })

    return results
