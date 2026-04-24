"""Tests for health check endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_basic_health(unauthed_client: AsyncClient):
    """Health endpoint should be public and return healthy."""
    response = await unauthed_client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "wellness-ops"


@pytest.mark.asyncio
async def test_db_health(unauthed_client: AsyncClient):
    """DB health check should work with test database."""
    response = await unauthed_client.get("/api/v1/health/db")
    assert response.status_code == 200
    data = response.json()
    assert data["component"] == "database"
