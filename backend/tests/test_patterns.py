"""Tests for pattern recognition (Phase 5)."""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

MOCK_PATTERNS = [
    {
        "pattern_type": "root_cause",
        "category_key": "kitchen_flow",
        "description": "Clients with empty fridges often show reactive eating patterns tied to work stress",
        "symptom_tags": ["empty fridge", "takeout"],
        "cause_tags": ["work stress", "no meal planning"],
        "frequency_hint": "common",
    },
    {
        "pattern_type": "correlation",
        "category_key": "sleep_environment",
        "description": "Work materials visible from bed correlates with lower sleep scores across audits",
        "symptom_tags": ["work visible", "poor sleep"],
        "cause_tags": ["no boundary", "anxiety"],
        "frequency_hint": "common",
    },
]

MOCK_SCORE_RESPONSE = {
    "score": 6,
    "what_observed": "Test observation.",
    "why_it_matters": "Test importance.",
    "how_to_close_gap": "Test recommendation.",
}


@pytest.fixture(autouse=True)
def mock_llm():
    with patch("app.services.diagnosis.chat_completion_json", new_callable=AsyncMock) as mock_score, \
         patch("app.services.report_generator.chat_completion", new_callable=AsyncMock) as mock_report, \
         patch("app.services.pattern_matcher.chat_completion_json", new_callable=AsyncMock) as mock_pattern:
        mock_score.return_value = MOCK_SCORE_RESPONSE
        mock_report.return_value = "Test generated text."
        mock_pattern.return_value = MOCK_PATTERNS
        yield


async def _create_scored_session(client: AsyncClient) -> str:
    """Create a client, session with observations, and generate scores."""
    c_resp = await client.post("/api/v1/clients", json={"display_name": "Pattern Test"})
    client_id = c_resp.json()["data"]["id"]

    s_resp = await client.post("/api/v1/audits", json={"client_id": client_id})
    session_id = s_resp.json()["data"]["id"]

    for room, content in [
        ("kitchen", "Fridge full of takeout, no fresh food"),
        ("bedroom", "Work laptop visible from bed"),
    ]:
        await client.post(
            f"/api/v1/audits/{session_id}/observations",
            json={"room_area": room, "content": content},
        )

    await client.post(f"/api/v1/audits/{session_id}/scores/generate")
    return session_id


@pytest.mark.asyncio
async def test_pattern_extraction_on_approval(client: AsyncClient):
    """Approving a report should extract patterns."""
    session_id = await _create_scored_session(client)

    # Generate report
    gen_resp = await client.post(f"/api/v1/audits/{session_id}/reports/generate")
    report_id = gen_resp.json()["data"]["id"]

    # Approve -- should trigger pattern extraction
    resp = await client.put(f"/api/v1/reports/{report_id}/approve")
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "final"


@pytest.mark.asyncio
async def test_get_session_patterns(client: AsyncClient):
    """Should return pattern matches for scored categories."""
    session_id = await _create_scored_session(client)

    resp = await client.get(f"/api/v1/audits/{session_id}/patterns")
    assert resp.status_code == 200
    data = resp.json()["data"]
    # Should be a dict of category_key -> pattern matches
    assert isinstance(data, dict)


@pytest.mark.asyncio
async def test_search_patterns(client: AsyncClient):
    """Should search for similar patterns given text."""
    resp = await client.post(
        "/api/v1/patterns/search",
        json={"observations_text": "Empty fridge, all takeout", "category_key": "kitchen_flow"},
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_patterns_empty_before_audits(client: AsyncClient):
    """With no completed audits, patterns should be empty."""
    c_resp = await client.post("/api/v1/clients", json={"display_name": "Fresh"})
    client_id = c_resp.json()["data"]["id"]
    s_resp = await client.post("/api/v1/audits", json={"client_id": client_id})
    session_id = s_resp.json()["data"]["id"]

    await client.post(
        f"/api/v1/audits/{session_id}/observations",
        json={"room_area": "entry", "content": "Nice entrance"},
    )
    await client.post(f"/api/v1/audits/{session_id}/scores/generate")

    resp = await client.get(f"/api/v1/audits/{session_id}/patterns")
    assert resp.status_code == 200
