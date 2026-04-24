"""Tests for knowledge management routes."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_domains_authenticated(client: AsyncClient):
    """Authenticated user should see domain stats."""
    response = await client.get("/api/v1/knowledge/domains")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    # Should return 7 domains
    assert len(data["data"]) == 7
    domain_names = [d["domain"] for d in data["data"]]
    assert "well" in domain_names
    assert "research" in domain_names
    assert "products" in domain_names


@pytest.mark.asyncio
async def test_list_domains_unauthenticated(unauthed_client: AsyncClient):
    """Unauthenticated request to domains should return 401."""
    response = await unauthed_client.get("/api/v1/knowledge/domains")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_documents_empty(client: AsyncClient):
    """Empty knowledge base should return empty list."""
    response = await client.get("/api/v1/knowledge/documents")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["data"] == []


@pytest.mark.asyncio
async def test_get_nonexistent_document(client: AsyncClient):
    """Getting a non-existent document should return 404."""
    response = await client.get(
        "/api/v1/knowledge/documents/00000000-0000-0000-0000-000000000000"
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_nonexistent_document(client: AsyncClient):
    """Deleting a non-existent document should return 404."""
    response = await client.delete(
        "/api/v1/knowledge/documents/00000000-0000-0000-0000-000000000000"
    )
    assert response.status_code == 404
