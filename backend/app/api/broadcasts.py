from app.api.deps import get_current_company_id
"""Broadcast API — send bulk messages to lead segments."""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.lead import Lead

router = APIRouter()


class BroadcastRequest(BaseModel):
    message: str
    filter_stage: str | None = None
    filter_priority: str | None = None
    filter_channel: str | None = None
    filter_tags: list[str] | None = None
    limit: int = 100


@router.post("/preview")
async def preview_broadcast(
    data: BroadcastRequest,
    company_id: uuid.UUID = Depends(get_current_company_id),
    db: AsyncSession = Depends(get_db),
):
    """Preview which leads would receive the broadcast."""
    query = select(Lead).where(Lead.company_id == company_id, Lead.is_active.is_(True))
    if data.filter_stage:
        query = query.where(Lead.stage == data.filter_stage)
    if data.filter_priority:
        query = query.where(Lead.priority == data.filter_priority)
    if data.filter_channel:
        query = query.where(Lead.source_channel == data.filter_channel)
    query = query.limit(data.limit)

    result = await db.execute(query)
    leads = result.scalars().all()

    return {
        "total_recipients": len(leads),
        "message_preview": data.message[:200],
        "recipients": [
            {
                "id": str(l.id),
                "name": l.name,
                "channel": l.source_channel,
                "phone": l.whatsapp_phone,
            }
            for l in leads
        ],
    }


@router.post("/send")
async def send_broadcast(
    data: BroadcastRequest,
    company_id: uuid.UUID = Depends(get_current_company_id),
    db: AsyncSession = Depends(get_db),
):
    """Send broadcast message to filtered leads."""
    from app.models.company import Company
    from app.models.conversation import Conversation
    from app.models.message import Message

    # Get company
    company_result = await db.execute(select(Company).where(Company.id == company_id))
    company = company_result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")

    # Get leads
    query = select(Lead).where(Lead.company_id == company_id, Lead.is_active.is_(True))
    if data.filter_stage:
        query = query.where(Lead.stage == data.filter_stage)
    if data.filter_priority:
        query = query.where(Lead.priority == data.filter_priority)
    if data.filter_channel:
        query = query.where(Lead.source_channel == data.filter_channel)
    query = query.limit(data.limit)

    result = await db.execute(query)
    leads = result.scalars().all()

    sent = 0
    failed = 0

    for lead in leads:
        # Find active conversation
        conv_result = await db.execute(
            select(Conversation).where(
                Conversation.lead_id == lead.id,
                Conversation.company_id == company_id,
                Conversation.status.in_(["active", "handed_off"]),
            ).limit(1)
        )
        conv = conv_result.scalar_one_or_none()
        if not conv:
            continue

        # Save message
        msg = Message(
            conversation_id=conv.id,
            direction="outbound",
            sender_type="human",
            msg_type="text",
            content=data.message,
        )
        db.add(msg)

        # Send via WhatsApp
        if lead.whatsapp_id and company.whatsapp_token:
            try:
                from app.services.whatsapp_client import send_text_message
                await send_text_message(
                    company.phone_number_id or "",
                    lead.whatsapp_id,
                    data.message,
                )
                sent += 1
            except Exception:
                failed += 1
        else:
            sent += 1  # Message saved even if not sent via WA

    await db.flush()

    return {
        "total_targeted": len(leads),
        "sent": sent,
        "failed": failed,
        "message": data.message[:100],
    }
