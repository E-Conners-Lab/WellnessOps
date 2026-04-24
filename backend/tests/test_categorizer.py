"""Tests for the free-form observation categorizer."""

import pytest
from httpx import AsyncClient

from app.services.categorizer import _fallback_categorization


class TestFallbackCategorization:
    """Tests for keyword-based fallback when LLM is unavailable."""

    def test_kitchen_keywords(self):
        """Kitchen-related text should map to kitchen room."""
        results = _fallback_categorization("The fridge is mostly empty, just condiments and takeout leftovers")
        assert results[0]["room_area"] == "kitchen"

    def test_bedroom_keywords(self):
        """Bedroom-related text should map to bedroom."""
        results = _fallback_categorization("The bed faces the window, no blackout curtains")
        assert results[0]["room_area"] == "bedroom"

    def test_workspace_keywords(self):
        """Workspace-related text should map to workspace."""
        results = _fallback_categorization("The desk chair is not ergonomic, just a dining chair")
        assert results[0]["room_area"] == "workspace"

    def test_entry_keywords(self):
        """Entry-related text should map to entry."""
        results = _fallback_categorization("The front door area has dead plants on the porch")
        assert results[0]["room_area"] == "entry"

    def test_low_confidence_returns_question(self):
        """Ambiguous text should return a clarifying question."""
        results = _fallback_categorization("Things seem a bit off here")
        assert results[0]["confidence"] < 0.7
        assert results[0]["clarifying_question"] is not None

    def test_wearable_keywords(self):
        """Wearable-related text should map to wearable."""
        results = _fallback_categorization("Her Oura ring shows HRV dropping over the past month")
        assert results[0]["room_area"] == "wearable"

    def test_hidden_spaces_keywords(self):
        """Hidden spaces text should map correctly."""
        results = _fallback_categorization("The closet is overflowing, the junk drawer won't close")
        assert results[0]["room_area"] == "hidden_spaces"

    def test_multi_room_detection(self):
        """Text mentioning multiple rooms should return multiple results."""
        results = _fallback_categorization(
            "The fridge has only condiments and the nightstand is covered in work papers"
        )
        rooms = [r["room_area"] for r in results]
        assert "kitchen" in rooms
        assert "bedroom" in rooms
        assert len(results) >= 2

    def test_always_returns_list(self):
        """Fallback should always return a list."""
        results = _fallback_categorization("just some random note")
        assert isinstance(results, list)

    def test_each_result_has_text_field(self):
        """Each result should include the text field."""
        results = _fallback_categorization("The fridge is empty")
        assert all("text" in r for r in results)


@pytest.mark.asyncio
async def test_categorize_endpoint_requires_auth(unauthed_client: AsyncClient):
    """Categorize endpoint should require authentication."""
    response = await unauthed_client.post(
        "/api/v1/observations/categorize",
        json={"text": "The kitchen fridge is empty"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_categorize_endpoint_validates_input(client: AsyncClient):
    """Empty text should fail validation."""
    response = await client.post(
        "/api/v1/observations/categorize",
        json={"text": ""},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_categorize_endpoint_returns_array(client: AsyncClient):
    """Categorize should return an array of results."""
    response = await client.post(
        "/api/v1/observations/categorize",
        json={"text": "The fridge is full of takeout containers and no fresh food"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert isinstance(data, list)
    assert len(data) >= 1
    assert "room_area" in data[0]
    assert "confidence" in data[0]
    assert "text" in data[0]
