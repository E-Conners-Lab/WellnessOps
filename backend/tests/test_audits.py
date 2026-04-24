"""Tests for audit session routes."""

import pytest
from httpx import AsyncClient


async def _create_client(client: AsyncClient) -> str:
    """Helper to create a test client and return its ID."""
    resp = await client.post(
        "/api/v1/clients",
        json={"display_name": "Audit Test Client"},
    )
    return resp.json()["data"]["id"]


@pytest.mark.asyncio
async def test_create_audit_session(client: AsyncClient):
    """Should create a new audit session."""
    client_id = await _create_client(client)
    response = await client.post(
        "/api/v1/audits",
        json={"client_id": client_id, "audit_tier": "core"},
    )
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["client_id"] == client_id
    assert data["audit_tier"] == "core"
    assert data["status"] == "in_progress"


@pytest.mark.asyncio
async def test_get_audit_session(client: AsyncClient):
    """Should retrieve session with observations array."""
    client_id = await _create_client(client)
    create_resp = await client.post(
        "/api/v1/audits",
        json={"client_id": client_id},
    )
    session_id = create_resp.json()["data"]["id"]

    get_resp = await client.get(f"/api/v1/audits/{session_id}")
    assert get_resp.status_code == 200
    data = get_resp.json()["data"]
    assert data["id"] == session_id
    assert "observations" in data


@pytest.mark.asyncio
async def test_advance_session_status(client: AsyncClient):
    """Should advance status through the workflow."""
    client_id = await _create_client(client)
    create_resp = await client.post(
        "/api/v1/audits",
        json={"client_id": client_id},
    )
    session_id = create_resp.json()["data"]["id"]

    # in_progress -> observations_complete
    resp = await client.put(
        f"/api/v1/audits/{session_id}/status",
        json={"target_status": "observations_complete"},
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "observations_complete"


@pytest.mark.asyncio
async def test_invalid_status_transition(client: AsyncClient):
    """Should reject invalid status transitions."""
    client_id = await _create_client(client)
    create_resp = await client.post(
        "/api/v1/audits",
        json={"client_id": client_id},
    )
    session_id = create_resp.json()["data"]["id"]

    # in_progress -> report_final (skipping steps)
    resp = await client.put(
        f"/api/v1/audits/{session_id}/status",
        json={"target_status": "report_final"},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_session_progress_empty(client: AsyncClient):
    """Empty session should show 0% progress."""
    client_id = await _create_client(client)
    create_resp = await client.post(
        "/api/v1/audits",
        json={"client_id": client_id},
    )
    session_id = create_resp.json()["data"]["id"]

    resp = await client.get(f"/api/v1/audits/{session_id}/progress")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["completion_percent"] == 0
    assert data["total_prompts"] > 0


@pytest.mark.asyncio
async def test_get_session_prompts(client: AsyncClient):
    """Should return prompt definitions for the session tier."""
    client_id = await _create_client(client)
    create_resp = await client.post(
        "/api/v1/audits",
        json={"client_id": client_id, "audit_tier": "core"},
    )
    session_id = create_resp.json()["data"]["id"]

    resp = await client.get(f"/api/v1/audits/{session_id}/prompts")
    assert resp.status_code == 200
    sections = resp.json()["data"]
    assert len(sections) > 0
    # First section should be entry
    assert sections[0]["room_area"] == "entry"
    assert len(sections[0]["prompts"]) == 3


@pytest.mark.asyncio
async def test_list_client_sessions(client: AsyncClient):
    """Should list sessions for a client."""
    client_id = await _create_client(client)
    await client.post("/api/v1/audits", json={"client_id": client_id})
    await client.post("/api/v1/audits", json={"client_id": client_id, "audit_tier": "extended"})

    resp = await client.get(f"/api/v1/clients/{client_id}/sessions")
    assert resp.status_code == 200
    assert len(resp.json()["data"]) == 2
