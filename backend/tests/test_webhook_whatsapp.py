import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_webhook_verify_success(client):
    """Test Meta webhook verification with correct token."""
    from app.config import settings
    settings.meta_verify_token = "test-token"

    response = await client.get(
        "/webhooks/whatsapp",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "test-token",
            "hub.challenge": "12345",
        },
    )
    assert response.status_code == 200
    assert response.json() == 12345


@pytest.mark.asyncio
async def test_webhook_verify_failure(client):
    """Test Meta webhook verification with wrong token."""
    from app.config import settings
    settings.meta_verify_token = "test-token"

    response = await client.get(
        "/webhooks/whatsapp",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "wrong-token",
            "hub.challenge": "12345",
        },
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_webhook_receive_empty(client):
    """Test receiving empty webhook payload."""
    response = await client.post(
        "/webhooks/whatsapp",
        json={"entry": []},
    )
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_webhook_receive_message_no_company(client):
    """Test receiving message when no company matches phone_number_id."""
    payload = {
        "entry": [
            {
                "changes": [
                    {
                        "field": "messages",
                        "value": {
                            "metadata": {"phone_number_id": "unknown"},
                            "contacts": [
                                {
                                    "wa_id": "5491155551234",
                                    "profile": {"name": "Test User"},
                                }
                            ],
                            "messages": [
                                {
                                    "from": "5491155551234",
                                    "id": "wamid.test123",
                                    "type": "text",
                                    "text": {"body": "Hola!"},
                                    "timestamp": "1710000000",
                                }
                            ],
                        },
                    }
                ]
            }
        ]
    }
    response = await client.post("/webhooks/whatsapp", json=payload)
    assert response.status_code == 200
