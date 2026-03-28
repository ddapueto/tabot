"""Tests for auth endpoints — register, login, refresh, me."""

import uuid

import pytest


@pytest.mark.asyncio
async def test_register_success(client, company_and_tokens):
    """Register a new user in an existing company."""
    unique = uuid.uuid4().hex[:8]
    response = await client.post(
        "/api/auth/register",
        json={
            "company_id": company_and_tokens["company_id"],
            "email": f"seller-{unique}@test.com",
            "name": "New Seller",
            "password": "password123",
            "role": "seller",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_register_duplicate_email(client, company_and_tokens):
    """Cannot register with the same email twice."""
    response = await client.post(
        "/api/auth/register",
        json={
            "company_id": company_and_tokens["company_id"],
            "email": company_and_tokens["email"],
            "name": "Duplicate",
            "password": "password123",
        },
    )
    assert response.status_code == 400
    assert "ya registrado" in response.json()["detail"]


@pytest.mark.asyncio
async def test_register_short_password(client, company_and_tokens):
    """Cannot register with password shorter than 8 chars."""
    response = await client.post(
        "/api/auth/register",
        json={
            "company_id": company_and_tokens["company_id"],
            "email": "short@test.com",
            "name": "Short Pass",
            "password": "123",
        },
    )
    assert response.status_code == 400
    assert "8 caracteres" in response.json()["detail"]


@pytest.mark.asyncio
async def test_login_success(client, company_and_tokens):
    """Login with correct credentials."""
    response = await client.post(
        "/api/auth/login",
        json={
            "company_id": company_and_tokens["company_id"],
            "email": company_and_tokens["email"],
            "password": company_and_tokens["password"],
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_login_wrong_password(client, company_and_tokens):
    """Login with wrong password returns 401."""
    response = await client.post(
        "/api/auth/login",
        json={
            "company_id": company_and_tokens["company_id"],
            "email": company_and_tokens["email"],
            "password": "wrongpassword",
        },
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_with_token(client, auth_headers):
    """GET /me with valid token returns user info."""
    response = await client.get("/api/auth/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "email" in data
    assert "company_id" in data
    assert data["role"] == "admin"


@pytest.mark.asyncio
async def test_me_without_token(client):
    """GET /me without token returns 401."""
    response = await client.get("/api/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token(client, company_and_tokens):
    """Refresh token returns new token pair."""
    response = await client.post(
        "/api/auth/refresh",
        json={"refresh_token": company_and_tokens["refresh_token"]},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
