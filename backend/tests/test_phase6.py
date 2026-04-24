"""Tests for Phase 6: auto-referrals, calibration, and polish."""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

MOCK_SCORE = {
    "score": 4,
    "what_observed": "Low score observation.",
    "why_it_matters": "Test.",
    "how_to_close_gap": "Fix it.",
}


@pytest.fixture(autouse=True)
def mock_llm():
    with patch("app.services.diagnosis.chat_completion_json", new_callable=AsyncMock) as m1, \
         patch("app.services.report_generator.chat_completion", new_callable=AsyncMock) as m2, \
         patch("app.services.pattern_matcher.chat_completion_json", new_callable=AsyncMock) as m3:
        m1.return_value = MOCK_SCORE
        m2.return_value = "Test text."
        m3.return_value = []
        yield


async def _setup_session(client: AsyncClient) -> str:
    c = await client.post("/api/v1/clients", json={"display_name": "P6 Test"})
    cid = c.json()["data"]["id"]
    s = await client.post("/api/v1/audits", json={"client_id": cid})
    sid = s.json()["data"]["id"]
    await client.post(f"/api/v1/audits/{sid}/observations", json={"room_area": "kitchen", "content": "Empty fridge"})
    await client.post(f"/api/v1/audits/{sid}/scores/generate")
    return sid


class TestAutoReferrals:
    @pytest.mark.asyncio
    async def test_referrals_endpoint(self, client: AsyncClient):
        """Should return referrals for scored session."""
        sid = await _setup_session(client)

        # Add a product that should match kitchen_flow
        await client.post("/api/v1/products", json={
            "name": "Meal Prep Kit",
            "category": "food",
            "why_recommended": "Helps with meal planning",
        })

        resp = await client.get(f"/api/v1/audits/{sid}/referrals")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "product_matches" in data
        assert "partner_matches" in data

    @pytest.mark.asyncio
    async def test_referrals_match_low_scores(self, client: AsyncClient):
        """Products should be matched to categories with low scores."""
        sid = await _setup_session(client)

        await client.post("/api/v1/products", json={
            "name": "Air Filter",
            "category": "air_quality",
            "why_recommended": "Reduces VOCs",
        })

        resp = await client.get(f"/api/v1/audits/{sid}/referrals")
        data = resp.json()["data"]
        # All mock scores are 4 (below 7), so air_quality products should match
        # to categories that map to air_quality (sleep_environment, natural_elements, sensory)
        all_products = []
        for prods in data["product_matches"].values():
            all_products.extend(prods)
        product_names = [p["name"] for p in all_products]
        assert "Air Filter" in product_names

    @pytest.mark.asyncio
    async def test_report_includes_referrals(self, client: AsyncClient):
        """Report generation should include auto-matched referrals."""
        sid = await _setup_session(client)

        resp = await client.post(f"/api/v1/audits/{sid}/reports/generate")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["priority_action_plan"] is not None
        # Referrals are embedded in the action plan
        assert "referrals" in data["priority_action_plan"]


class TestCalibration:
    @pytest.mark.asyncio
    async def test_calibration_endpoint(self, client: AsyncClient):
        """Should return calibration stats."""
        await _setup_session(client)

        resp = await client.get("/api/v1/calibration")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "total_scores" in data
        assert "total_overrides" in data
        assert "overall_override_rate" in data
        assert "categories" in data

    @pytest.mark.asyncio
    async def test_calibration_tracks_overrides(self, client: AsyncClient):
        """Override rate should increase after overrides."""
        sid = await _setup_session(client)

        # Override a score
        await client.put(
            f"/api/v1/audits/{sid}/scores/kitchen_flow/override",
            json={"score": 2, "override_notes": "Worse than AI thought"},
        )

        resp = await client.get("/api/v1/calibration")
        data = resp.json()["data"]
        assert data["total_overrides"] >= 1

    @pytest.mark.asyncio
    async def test_calibration_empty_without_audits(self, client: AsyncClient):
        """Calibration should work with no data."""
        resp = await client.get("/api/v1/calibration")
        assert resp.status_code == 200
        assert resp.json()["data"]["total_scores"] >= 0
