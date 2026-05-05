import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_liveness_check(async_client: AsyncClient) -> None:
    response = await async_client.get("/health/live")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "alive"


@pytest.mark.asyncio
async def test_readiness_check(async_client: AsyncClient) -> None:
    response = await async_client.get("/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"


@pytest.mark.asyncio
async def test_root_endpoint(async_client: AsyncClient) -> None:
    response = await async_client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "version" in data
    assert "environment" in data
    assert data["name"] == "FastAPI Application"
