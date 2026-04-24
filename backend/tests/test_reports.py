"""Tests for score generation, reports, products, and partners."""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient


MOCK_SCORE_RESPONSE = {
    "score": 6,
    "what_observed": "Test observation summary.",
    "why_it_matters": "Test explanation of importance.",
    "how_to_close_gap": "Test recommendation.",
}


@pytest.fixture(autouse=True)
def mock_llm():
    """Mock LLM calls for deterministic testing."""
    with patch("app.services.diagnosis.chat_completion_json", new_callable=AsyncMock) as mock_json, \
         patch("app.services.report_generator.chat_completion", new_callable=AsyncMock) as mock_text:
        mock_json.return_value = MOCK_SCORE_RESPONSE
        mock_text.return_value = "Test generated text for report section."
        yield mock_json, mock_text


async def _create_session_with_observations(client: AsyncClient) -> str:
    """Helper: create client, session, add observations, return session_id."""
    c_resp = await client.post("/api/v1/clients", json={"display_name": "Report Test"})
    client_id = c_resp.json()["data"]["id"]

    s_resp = await client.post("/api/v1/audits", json={"client_id": client_id})
    session_id = s_resp.json()["data"]["id"]

    # Add observations across multiple rooms
    for room, content in [
        ("entry", "Clean entrance, good first impression"),
        ("kitchen", "Fridge has mostly takeout, no meal planning system"),
        ("bedroom", "Phone on nightstand, no blackout curtains"),
        ("living", "Good natural light, some plants"),
        ("hidden_spaces", "Closet overflowing, junk drawer packed"),
        ("workspace", "Borrowed corner of dining table, no proper chair"),
    ]:
        await client.post(
            f"/api/v1/audits/{session_id}/observations",
            json={"room_area": room, "content": content},
        )

    return session_id


class TestScoreGeneration:
    @pytest.mark.asyncio
    async def test_generate_scores(self, client: AsyncClient):
        """Should generate scores for all core categories."""
        session_id = await _create_session_with_observations(client)

        resp = await client.post(f"/api/v1/audits/{session_id}/scores/generate")
        assert resp.status_code == 200
        scores = resp.json()["data"]
        assert len(scores) == 10  # core has 10 categories
        for score in scores:
            assert 1 <= score["score"] <= 10
            assert score["status_label"]
            assert score["category_key"]

    @pytest.mark.asyncio
    async def test_get_scores(self, client: AsyncClient):
        """Should retrieve generated scores."""
        session_id = await _create_session_with_observations(client)
        await client.post(f"/api/v1/audits/{session_id}/scores/generate")

        resp = await client.get(f"/api/v1/audits/{session_id}/scores")
        assert resp.status_code == 200
        assert len(resp.json()["data"]) == 10

    @pytest.mark.asyncio
    async def test_override_score(self, client: AsyncClient):
        """Should allowthe practitioner to override a score."""
        session_id = await _create_session_with_observations(client)
        await client.post(f"/api/v1/audits/{session_id}/scores/generate")

        resp = await client.put(
            f"/api/v1/audits/{session_id}/scores/kitchen_flow/override",
            json={"score": 3, "override_notes": "Worse than AI thought"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["score"] == 3
        assert data["practitioner_override"] is True
        assert data["override_notes"] == "Worse than AI thought"


class TestReportGeneration:
    @pytest.mark.asyncio
    async def test_generate_report(self, client: AsyncClient):
        """Should generate a report from scored data."""
        session_id = await _create_session_with_observations(client)
        await client.post(f"/api/v1/audits/{session_id}/scores/generate")

        resp = await client.post(f"/api/v1/audits/{session_id}/reports/generate")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert 0 <= data["overall_score"] <= 100
        assert data["overall_label"]
        assert data["status"] == "draft"
        assert data["priority_action_plan"]
        assert data["vision_section"]
        assert data["next_steps"]

    @pytest.mark.asyncio
    async def test_edit_report(self, client: AsyncClient):
        """Should allow editing draft report sections."""
        session_id = await _create_session_with_observations(client)
        await client.post(f"/api/v1/audits/{session_id}/scores/generate")
        gen_resp = await client.post(f"/api/v1/audits/{session_id}/reports/generate")
        report_id = gen_resp.json()["data"]["id"]

        resp = await client.put(
            f"/api/v1/reports/{report_id}",
            json={"vision_section": "Custom vision text from the practitioner"},
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["vision_section"] == "Custom vision text from the practitioner"

    @pytest.mark.asyncio
    async def test_preview_report(self, client: AsyncClient):
        """Preview should include report data and scores."""
        session_id = await _create_session_with_observations(client)
        await client.post(f"/api/v1/audits/{session_id}/scores/generate")
        gen_resp = await client.post(f"/api/v1/audits/{session_id}/reports/generate")
        report_id = gen_resp.json()["data"]["id"]

        resp = await client.get(f"/api/v1/reports/{report_id}/preview")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "scores" in data
        assert len(data["scores"]) == 10


class TestProducts:
    @pytest.mark.asyncio
    async def test_crud_product(self, client: AsyncClient):
        """Should create, list, update, and deactivate a product."""
        # Create
        resp = await client.post(
            "/api/v1/products",
            json={"name": "Air Purifier", "category": "air_quality", "why_recommended": "Reduces VOCs"},
        )
        assert resp.status_code == 201
        product_id = resp.json()["data"]["id"]

        # List
        resp = await client.get("/api/v1/products")
        assert resp.status_code == 200
        assert len(resp.json()["data"]) >= 1

        # Update
        resp = await client.put(
            f"/api/v1/products/{product_id}",
            json={"price_range": "$200-400"},
        )
        assert resp.status_code == 200

        # Deactivate
        resp = await client.delete(f"/api/v1/products/{product_id}")
        assert resp.status_code == 200


class TestPartners:
    @pytest.mark.asyncio
    async def test_crud_partner(self, client: AsyncClient):
        """Should create, list, update, and deactivate a partner."""
        resp = await client.post(
            "/api/v1/partners",
            json={"name": "Jane Smith", "category": "organizer", "why_recommended": "Expert organizer"},
        )
        assert resp.status_code == 201
        partner_id = resp.json()["data"]["id"]

        resp = await client.get("/api/v1/partners")
        assert resp.status_code == 200
        assert len(resp.json()["data"]) >= 1

        resp = await client.put(
            f"/api/v1/partners/{partner_id}",
            json={"location": "Nashville, TN"},
        )
        assert resp.status_code == 200

        resp = await client.delete(f"/api/v1/partners/{partner_id}")
        assert resp.status_code == 200
