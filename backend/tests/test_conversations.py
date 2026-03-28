"""Tests for conversations endpoints — list, send message."""

import uuid

import pytest


@pytest.mark.asyncio
async def test_list_conversations_empty(client, auth_headers):
    """List conversations for new company returns empty."""
    response = await client.get(
        "/api/conversations/", headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_send_message_nonexistent(client, auth_headers):
    """Send message to non-existent conversation returns 404."""
    fake_id = uuid.uuid4()
    response = await client.post(
        f"/api/conversations/{fake_id}/send",
        headers=auth_headers,
        json={"content": "Hola!", "msg_type": "text"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_send_message_success(client, auth_headers, company_and_tokens):
    """Send a human message in an existing conversation."""
    from app.database import async_session
    from app.models.conversation import Conversation
    from app.models.lead import Lead

    company_id = uuid.UUID(company_and_tokens["company_id"])

    async with async_session() as db:
        lead = Lead(
            company_id=company_id,
            name="Conv Test Lead",
            whatsapp_phone="+598990001111",
            whatsapp_id="598990001111",
            source_channel="whatsapp",
            stage="new",
            score=0,
        )
        db.add(lead)
        await db.flush()

        conv = Conversation(
            lead_id=lead.id,
            company_id=company_id,
            channel="whatsapp",
            status="active",
            ai_enabled=True,
        )
        db.add(conv)
        await db.commit()
        await db.refresh(conv)
        conv_id = str(conv.id)

    response = await client.post(
        f"/api/conversations/{conv_id}/send",
        headers=auth_headers,
        json={"content": "Hola, te contacto por tu consulta"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["content"] == "Hola, te contacto por tu consulta"
    assert data["sender_type"] == "human"
    assert "id" in data


@pytest.mark.asyncio
async def test_get_conversation_messages(client, auth_headers, company_and_tokens):
    """Get messages for an existing conversation."""
    from app.database import async_session
    from app.models.conversation import Conversation
    from app.models.lead import Lead
    from app.models.message import Message

    company_id = uuid.UUID(company_and_tokens["company_id"])

    async with async_session() as db:
        lead = Lead(
            company_id=company_id,
            name="Msg Test Lead",
            whatsapp_phone="+598990002222",
            whatsapp_id="598990002222",
            source_channel="whatsapp",
            stage="new",
            score=0,
        )
        db.add(lead)
        await db.flush()

        conv = Conversation(
            lead_id=lead.id,
            company_id=company_id,
            channel="whatsapp",
            status="active",
            ai_enabled=True,
        )
        db.add(conv)
        await db.flush()

        msg = Message(
            conversation_id=conv.id,
            direction="inbound",
            sender_type="lead",
            msg_type="text",
            content="Hola, quiero info",
        )
        db.add(msg)
        await db.commit()
        conv_id = str(conv.id)

    response = await client.get(
        f"/api/conversations/{conv_id}/messages",
        headers=auth_headers,
    )
    assert response.status_code == 200
    messages = response.json()
    assert len(messages) >= 1
    assert messages[0]["content"] == "Hola, quiero info"
