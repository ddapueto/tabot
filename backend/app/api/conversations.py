import asyncio
import json
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.conversation import Conversation
from app.models.lead import Lead
from app.models.message import Message
from app.schemas.conversation import ConversationResponse, ConversationWithMessages, MessageResponse

router = APIRouter()

# Simple in-memory pub/sub for SSE (replace with Redis pub/sub in production)
_listeners: dict[str, list[asyncio.Queue]] = {}


def _notify(company_id: str, event: dict):
    """Notify all SSE listeners for a company."""
    for queue in _listeners.get(company_id, []):
        queue.put_nowait(event)


class SendMessageRequest(BaseModel):
    content: str
    msg_type: str = "text"


@router.get("/{company_id}", response_model=list[dict])
async def list_conversations(
    company_id: uuid.UUID,
    status: str | None = None,
    channel: str | None = None,
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List conversations with lead info."""
    query = (
        select(Conversation, Lead.name, Lead.whatsapp_phone, Lead.instagram_username, Lead.score, Lead.priority)
        .join(Lead, Conversation.lead_id == Lead.id)
        .where(Conversation.company_id == company_id)
    )
    if status:
        query = query.where(Conversation.status == status)
    if channel:
        query = query.where(Conversation.channel == channel)
    query = query.order_by(Conversation.updated_at.desc()).limit(limit).offset(offset)

    result = await db.execute(query)
    rows = result.all()
    return [
        {
            "id": str(conv.id),
            "lead_id": str(conv.lead_id),
            "company_id": str(conv.company_id),
            "channel": conv.channel,
            "status": conv.status,
            "ai_enabled": conv.ai_enabled,
            "summary": conv.summary,
            "topic": conv.topic,
            "created_at": conv.created_at.isoformat(),
            "updated_at": conv.updated_at.isoformat(),
            "lead_name": name,
            "lead_phone": phone,
            "lead_instagram": ig,
            "lead_score": score,
            "lead_priority": priority,
        }
        for conv, name, phone, ig, score, priority in rows
    ]


@router.get("/{company_id}/{conversation_id}", response_model=ConversationWithMessages)
async def get_conversation(
    company_id: uuid.UUID,
    conversation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Conversation)
        .where(Conversation.id == conversation_id, Conversation.company_id == company_id)
        .options(selectinload(Conversation.messages))
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversacion no encontrada")
    return conversation


@router.get("/{company_id}/{conversation_id}/messages", response_model=list[MessageResponse])
async def list_messages(
    company_id: uuid.UUID,
    conversation_id: uuid.UUID,
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    conv_result = await db.execute(
        select(Conversation.id)
        .where(Conversation.id == conversation_id, Conversation.company_id == company_id)
    )
    if not conv_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Conversacion no encontrada")

    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
        .limit(limit)
        .offset(offset)
    )
    return result.scalars().all()


@router.post("/{company_id}/{conversation_id}/send")
async def send_human_message(
    company_id: uuid.UUID,
    conversation_id: uuid.UUID,
    data: SendMessageRequest,
    db: AsyncSession = Depends(get_db),
):
    """Send a message as a human agent in a conversation."""
    # Verify conversation
    result = await db.execute(
        select(Conversation)
        .where(Conversation.id == conversation_id, Conversation.company_id == company_id)
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversacion no encontrada")

    # Save message
    msg = Message(
        conversation_id=conversation.id,
        direction="outbound",
        sender_type="human",
        msg_type=data.msg_type,
        content=data.content,
    )
    db.add(msg)

    # Update lead last_response_at
    lead_result = await db.execute(select(Lead).where(Lead.id == conversation.lead_id))
    lead = lead_result.scalar_one_or_none()
    if lead:
        lead.last_response_at = datetime.now(timezone.utc)

    # Update conversation timestamp
    conversation.updated_at = datetime.now(timezone.utc)

    await db.flush()
    await db.refresh(msg)

    # Send via WhatsApp if configured
    if conversation.channel == "whatsapp" and lead and lead.whatsapp_id:
        from app.config import settings
        from app.models.company import Company

        company_result = await db.execute(select(Company).where(Company.id == company_id))
        company = company_result.scalar_one_or_none()
        if company and company.whatsapp_token:
            try:
                from app.services.whatsapp_client import send_text_message
                await send_text_message(
                    company.phone_number_id or "",
                    lead.whatsapp_id,
                    data.content,
                )
            except Exception:
                pass  # Log but don't fail the dashboard send

    # Notify SSE listeners
    _notify(str(company_id), {
        "type": "new_message",
        "conversation_id": str(conversation_id),
        "message": {
            "id": str(msg.id),
            "direction": "outbound",
            "sender_type": "human",
            "content": data.content,
            "created_at": msg.created_at.isoformat(),
        },
    })

    return {
        "id": str(msg.id),
        "content": data.content,
        "sender_type": "human",
        "created_at": msg.created_at.isoformat(),
    }


@router.get("/{company_id}/events/stream")
async def sse_stream(company_id: uuid.UUID, request: Request):
    """Server-Sent Events stream for real-time updates."""
    queue: asyncio.Queue = asyncio.Queue()
    key = str(company_id)

    if key not in _listeners:
        _listeners[key] = []
    _listeners[key].append(queue)

    async def event_generator():
        try:
            yield f"data: {json.dumps({'type': 'connected'})}\n\n"
            while True:
                if await request.is_disconnected():
                    break
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield f"data: {json.dumps(event)}\n\n"
                except asyncio.TimeoutError:
                    yield f"data: {json.dumps({'type': 'ping'})}\n\n"
        finally:
            _listeners[key].remove(queue)
            if not _listeners[key]:
                del _listeners[key]

    return StreamingResponse(event_generator(), media_type="text/event-stream")
