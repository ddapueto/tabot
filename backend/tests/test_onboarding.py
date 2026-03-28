"""Tests for onboarding — company setup in one step."""

import uuid

import pytest


@pytest.mark.asyncio
async def test_onboarding_success(client):
    """Create a new company with admin user."""
    unique = uuid.uuid4().hex[:8]
    response = await client.post(
        "/api/onboarding/setup",
        json={
            "company_name": f"Onboard Test {unique}",
            "business_type": "servicios",
            "admin_name": "Admin Test",
            "admin_email": f"onboard-{unique}@test.com",
            "admin_password": "securepass123",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "company_id" in data
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["company_name"] == f"Onboard Test {unique}"


@pytest.mark.asyncio
async def test_onboarding_short_password(client):
    """Onboarding with short password fails."""
    response = await client.post(
        "/api/onboarding/setup",
        json={
            "company_name": "Fail Co",
            "business_type": "retail",
            "admin_name": "Admin",
            "admin_email": "fail@test.com",
            "admin_password": "123",
        },
    )
    assert response.status_code == 400
    assert "8 caracteres" in response.json()["detail"]
