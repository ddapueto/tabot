"""Shared fixtures for all tests."""

import uuid

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest_asyncio.fixture(loop_scope="session")
async def client():
    """Async HTTP client for testing."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture(loop_scope="session")
async def company_and_tokens(client: AsyncClient) -> dict:
    """Create a fresh company via onboarding and return tokens + company_id."""
    unique = uuid.uuid4().hex[:8]
    response = await client.post(
        "/api/onboarding/setup",
        json={
            "company_name": f"Test Co {unique}",
            "business_type": "retail",
            "admin_name": "Test Admin",
            "admin_email": f"admin-{unique}@test.com",
            "admin_password": "testpass123",
        },
    )
    assert response.status_code == 200, response.text
    data = response.json()
    return {
        "company_id": data["company_id"],
        "access_token": data["access_token"],
        "refresh_token": data["refresh_token"],
        "email": f"admin-{unique}@test.com",
        "password": "testpass123",
    }


@pytest_asyncio.fixture(loop_scope="session")
async def auth_headers(company_and_tokens: dict) -> dict:
    """Authorization headers with valid JWT."""
    return {"Authorization": f"Bearer {company_and_tokens['access_token']}"}
