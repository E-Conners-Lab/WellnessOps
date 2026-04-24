"""Tests for authentication routes."""

import pytest
from httpx import AsyncClient

from app.db.models.user import User


@pytest.mark.asyncio
async def test_login_success(unauthed_client: AsyncClient, test_user: User):
    """Valid credentials should return user data and set cookies."""
    response = await unauthed_client.post(
        "/api/v1/auth/login",
        json={"email": "test@wellnessops.local", "password": "testpassword123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["data"]["email"] == "test@wellnessops.local"
    assert "access_token" in response.cookies
    assert "refresh_token" in response.cookies


@pytest.mark.asyncio
async def test_login_wrong_password(unauthed_client: AsyncClient, test_user: User):
    """Wrong password should return 401."""
    response = await unauthed_client.post(
        "/api/v1/auth/login",
        json={"email": "test@wellnessops.local", "password": "wrongpassword1"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent_user(unauthed_client: AsyncClient):
    """Non-existent email should return 401."""
    response = await unauthed_client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@example.com", "password": "testpassword123"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_validation_short_password(unauthed_client: AsyncClient):
    """Password shorter than 8 chars should fail validation."""
    response = await unauthed_client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "short"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_me_authenticated(client: AsyncClient, test_user: User):
    """Authenticated request to /me should return user data."""
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["email"] == "test@wellnessops.local"


@pytest.mark.asyncio
async def test_get_me_unauthenticated(unauthed_client: AsyncClient):
    """Unauthenticated request to /me should return 401."""
    response = await unauthed_client.get("/api/v1/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_logout(client: AsyncClient):
    """Logout should clear cookies."""
    response = await client.post("/api/v1/auth/logout")
    assert response.status_code == 200
    assert response.json()["data"]["message"] == "Logged out"


@pytest.mark.asyncio
async def test_refresh_without_token(unauthed_client: AsyncClient):
    """Refresh without a token should return 401."""
    response = await unauthed_client.post("/api/v1/auth/refresh")
    assert response.status_code == 401
