"""Tests for client management routes."""

import pytest
from httpx import AsyncClient

from app.db.models.user import User


@pytest.mark.asyncio
async def test_list_clients_empty(client: AsyncClient):
    """Empty client list should return empty array."""
    response = await client.get("/api/v1/clients")
    assert response.status_code == 200
    assert response.json()["data"] == []


@pytest.mark.asyncio
async def test_create_client(client: AsyncClient):
    """Should create a new client and return it."""
    response = await client.post(
        "/api/v1/clients",
        json={"display_name": "Test Client", "budget_tier": "moderate"},
    )
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["display_name"] == "Test Client"
    assert data["budget_tier"] == "moderate"
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_create_and_get_client(client: AsyncClient):
    """Should be able to retrieve a created client."""
    create_resp = await client.post(
        "/api/v1/clients",
        json={"display_name": "Jane Doe"},
    )
    client_id = create_resp.json()["data"]["id"]

    get_resp = await client.get(f"/api/v1/clients/{client_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["data"]["display_name"] == "Jane Doe"


@pytest.mark.asyncio
async def test_update_client(client: AsyncClient):
    """Should update client fields."""
    create_resp = await client.post(
        "/api/v1/clients",
        json={"display_name": "Original Name"},
    )
    client_id = create_resp.json()["data"]["id"]

    update_resp = await client.put(
        f"/api/v1/clients/{client_id}",
        json={"display_name": "Updated Name", "has_wearable": True},
    )
    assert update_resp.status_code == 200
    data = update_resp.json()["data"]
    assert data["display_name"] == "Updated Name"
    assert data["has_wearable"] is True


@pytest.mark.asyncio
async def test_soft_delete_client(client: AsyncClient):
    """Soft delete should hide client from list."""
    create_resp = await client.post(
        "/api/v1/clients",
        json={"display_name": "To Delete"},
    )
    client_id = create_resp.json()["data"]["id"]

    del_resp = await client.delete(f"/api/v1/clients/{client_id}")
    assert del_resp.status_code == 200

    # Should not appear in list
    list_resp = await client.get("/api/v1/clients")
    ids = [c["id"] for c in list_resp.json()["data"]]
    assert client_id not in ids


@pytest.mark.asyncio
async def test_get_nonexistent_client(client: AsyncClient):
    """Getting a non-existent client should return 404."""
    response = await client.get("/api/v1/clients/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_unauthenticated_access(unauthed_client: AsyncClient):
    """Unauthenticated requests should return 401."""
    response = await unauthed_client.get("/api/v1/clients")
    assert response.status_code == 401
