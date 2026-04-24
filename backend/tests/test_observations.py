"""Tests for observation routes."""

import pytest
from httpx import AsyncClient


async def _create_session(client: AsyncClient) -> tuple[str, str]:
    """Helper to create a client and session, return (client_id, session_id)."""
    c_resp = await client.post(
        "/api/v1/clients",
        json={"display_name": "Obs Test Client"},
    )
    client_id = c_resp.json()["data"]["id"]

    s_resp = await client.post(
        "/api/v1/audits",
        json={"client_id": client_id},
    )
    session_id = s_resp.json()["data"]["id"]
    return client_id, session_id


@pytest.mark.asyncio
async def test_add_observation(client: AsyncClient):
    """Should add a single observation to a session."""
    _, session_id = await _create_session(client)

    response = await client.post(
        f"/api/v1/audits/{session_id}/observations",
        json={
            "room_area": "entry",
            "content": "Beautiful garden at the entrance",
            "prompt_key": "entry_first_impression",
        },
    )
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["room_area"] == "entry"
    assert data["content"] == "Beautiful garden at the entrance"
    assert data["prompt_key"] == "entry_first_impression"


@pytest.mark.asyncio
async def test_update_observation(client: AsyncClient):
    """Should update an observation's content."""
    _, session_id = await _create_session(client)

    create_resp = await client.post(
        f"/api/v1/audits/{session_id}/observations",
        json={"room_area": "kitchen", "content": "Original note"},
    )
    obs_id = create_resp.json()["data"]["id"]

    update_resp = await client.put(
        f"/api/v1/observations/{obs_id}",
        json={"content": "Updated note with more detail"},
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["data"]["content"] == "Updated note with more detail"


@pytest.mark.asyncio
async def test_delete_observation(client: AsyncClient):
    """Should delete an observation."""
    _, session_id = await _create_session(client)

    create_resp = await client.post(
        f"/api/v1/audits/{session_id}/observations",
        json={"room_area": "bedroom", "content": "To be deleted"},
    )
    obs_id = create_resp.json()["data"]["id"]

    del_resp = await client.delete(f"/api/v1/observations/{obs_id}")
    assert del_resp.status_code == 200


@pytest.mark.asyncio
async def test_bulk_add_observations(client: AsyncClient):
    """Should bulk add observations from a room section."""
    _, session_id = await _create_session(client)

    response = await client.post(
        f"/api/v1/audits/{session_id}/observations/bulk",
        json={
            "observations": [
                {"room_area": "entry", "content": "Great curb appeal", "prompt_key": "entry_first_impression", "sort_order": 0},
                {"room_area": "entry", "content": "Welcoming door", "prompt_key": "entry_communication", "sort_order": 1},
                {"room_area": "entry", "prompt_key": "entry_threshold", "skipped": True, "sort_order": 2},
            ]
        },
    )
    assert response.status_code == 201
    data = response.json()["data"]
    assert len(data) == 3
    assert data[2]["skipped"] is True


@pytest.mark.asyncio
async def test_skip_observation(client: AsyncClient):
    """Should record a skipped prompt."""
    _, session_id = await _create_session(client)

    response = await client.post(
        f"/api/v1/audits/{session_id}/observations",
        json={
            "room_area": "workspace",
            "prompt_key": "workspace_dedicated",
            "skipped": True,
        },
    )
    assert response.status_code == 201
    assert response.json()["data"]["skipped"] is True


@pytest.mark.asyncio
async def test_progress_updates_with_observations(client: AsyncClient):
    """Progress should update as observations are added."""
    _, session_id = await _create_session(client)

    # Check initial progress
    prog_resp = await client.get(f"/api/v1/audits/{session_id}/progress")
    assert prog_resp.json()["data"]["completed_prompts"] == 0

    # Add an observation
    await client.post(
        f"/api/v1/audits/{session_id}/observations",
        json={"room_area": "entry", "content": "Nice", "prompt_key": "entry_first_impression"},
    )

    # Check updated progress
    prog_resp = await client.get(f"/api/v1/audits/{session_id}/progress")
    assert prog_resp.json()["data"]["completed_prompts"] == 1
    assert prog_resp.json()["data"]["completion_percent"] > 0


@pytest.mark.asyncio
async def test_cannot_add_to_completed_session(client: AsyncClient):
    """Should not allow adding observations to a non-in_progress session."""
    _, session_id = await _create_session(client)

    # Advance status
    await client.put(
        f"/api/v1/audits/{session_id}/status",
        json={"target_status": "observations_complete"},
    )

    # Try to add observation
    response = await client.post(
        f"/api/v1/audits/{session_id}/observations",
        json={"room_area": "entry", "content": "Late addition"},
    )
    assert response.status_code == 400
