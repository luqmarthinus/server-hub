"""
Tests for authentication endpoints: registration, login, token verification.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import verify_password, create_access_token
from src.models.user import User


@pytest.mark.asyncio
async def test_register_success(async_client: AsyncClient):
    """Test successful user registration."""
    response = await async_client.post(
        "/api/auth/register",
        json={
            "email": "test@example.com",
            "password": "SecurePass123",
            "full_name": "Test User",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["full_name"] == "Test User"
    assert "id" in data
    assert "password" not in data  # password should not be returned


@pytest.mark.asyncio
async def test_register_duplicate_email(async_client: AsyncClient):
    """Test registration with existing email returns 400."""
    # First registration
    await async_client.post(
        "/api/auth/register",
        json={
            "email": "duplicate@example.com",
            "password": "SecurePass123",
            "full_name": "First User",
        },
    )
    # Second registration with same email
    response = await async_client.post(
        "/api/auth/register",
        json={
            "email": "duplicate@example.com",
            "password": "AnotherPass456",
            "full_name": "Second User",
        },
    )
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_register_invalid_email(async_client: AsyncClient):
    """Test registration with malformed email returns 422."""
    response = await async_client.post(
        "/api/auth/register",
        json={
            "email": "not-an-email",
            "password": "SecurePass123",
            "full_name": "Test User",
        },
    )
    assert response.status_code == 422  # Pydantic validation error


@pytest.mark.asyncio
async def test_login_success(async_client: AsyncClient):
    """Test login with valid credentials returns access token."""
    # First register a user
    await async_client.post(
        "/api/auth/register",
        json={
            "email": "login@example.com",
            "password": "CorrectPass123",
            "full_name": "Login User",
        },
    )
    # Then login
    response = await async_client.post(
        "/api/auth/login",
        data={  # OAuth2 form data
            "username": "login@example.com",
            "password": "CorrectPass123",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(async_client: AsyncClient):
    """Test login with incorrect password returns 401."""
    await async_client.post(
        "/api/auth/register",
        json={
            "email": "wrongpass@example.com",
            "password": "RealPass123",
            "full_name": "Wrong Pass User",
        },
    )
    response = await async_client.post(
        "/api/auth/login",
        data={
            "username": "wrongpass@example.com",
            "password": "WrongPass123",
        },
    )
    assert response.status_code == 401
    assert "incorrect email or password" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_login_nonexistent_user(async_client: AsyncClient):
    """Test login with non-existent email returns 401."""
    response = await async_client.post(
        "/api/auth/login",
        data={
            "username": "nonexistent@example.com",
            "password": "AnyPass123",
        },
    )
    assert response.status_code == 401
    assert "incorrect email or password" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_me_with_token(async_client: AsyncClient):
    """Test accessing /me with valid token returns user info."""
    # Register and login
    await async_client.post(
        "/api/auth/register",
        json={
            "email": "me@example.com",
            "password": "MyPass123",
            "full_name": "Me User",
        },
    )
    login_resp = await async_client.post(
        "/api/auth/login",
        data={
            "username": "me@example.com",
            "password": "MyPass123",
        },
    )
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    response = await async_client.get("/api/auth/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "me@example.com"
    assert data["full_name"] == "Me User"


@pytest.mark.asyncio
async def test_get_me_no_token(async_client: AsyncClient):
    """Test accessing /me without token returns 401."""
    response = await async_client.get("/api/auth/me")
    assert response.status_code == 401
    assert "not authenticated" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_me_invalid_token(async_client: AsyncClient):
    """Test accessing /me with invalid token returns 401."""
    headers = {"Authorization": "Bearer invalid.token.here"}
    response = await async_client.get("/api/auth/me", headers=headers)
    assert response.status_code == 401
    assert "invalid token" in response.json()["detail"].lower()