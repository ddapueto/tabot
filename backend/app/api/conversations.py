import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.conversation import Conversation
from app.models.message import Message
from app.schemas.conversation import ConversationResponse, ConversationWithMessages, MessageResponse

router = APIRouter()


@router.get("/{company_id}", response_model=list[ConversationResponse])
async def list_conversations(
    company_id: uuid.UUID,
    status: str | None = None,
    channel: str | None = None,
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    query = select(Conversation).where(Conversation.company_id == company_id)
    if status:
        query = query.where(Conversation.status == status)
    if channel:
        query = query.where(Conversation.channel == channel)
    query = query.order_by(Conversation.updated_at.desc())
    query = query.limit(limit).offset(offset)

    result = await db.execute(query)
    return result.scalars().all()


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
    # Verify conversation belongs to company
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
