"""Broadcast API — send bulk messages to lead segments."""

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_company_id
from app.database import get_db
from app.models.company import Company
from app.models.conversation import Conversation
from app.models.lead import Lead
from app.models.message import Message
from app.services.whatsapp_client import send_text_message

logger = logging.getLogger(__name__)
router = APIRouter()


class BroadcastRequest(BaseModel):
    message: str
    filter_stage: str | None = None
    filter_priority: str | None = None
    filter_channel: str | None = None
    filter_tags: list[str] | None = None
    limit: int = 100


def _build_leads_query(company_id: uuid.UUID, data: BroadcastRequest):
    """Build filtered query for broadcast leads."""
    query = select(Lead).where(Lead.company_id == company_id, Lead.is_active.is_(True))
    if data.filter_stage:
        query = query.where(Lead.stage == data.filter_stage)
    if data.filter_priority:
        query = query.where(Lead.priority == data.filter_priority)
    if data.filter_channel:
        query = query.where(Lead.source_channel == data.filter_channel)
    return query.limit(data.limit)


@router.post("/preview")
async def preview_broadcast(
    data: BroadcastRequest,
    company_id: uuid.UUID = Depends(get_current_company_id),
    db: AsyncSession = Depends(get_db),
):
    """Preview which leads would receive the broadcast."""
    result = await db.execute(_build_leads_query(company_id, data))
    leads = result.scalars().all()

    return {
        "total_recipients": len(leads),
        "message_preview": data.message[:200],
        "recipients": [
            {
                "id": str(lead.id),
                "name": lead.name,
                "channel": lead.source_channel,
                "phone": lead.whatsapp_phone,
            }
            for lead in leads
        ],
    }


@router.post("/send")
async def send_broadcast(
    data: BroadcastRequest,
    company_id: uuid.UUID = Depends(get_current_company_id),
    db: AsyncSession = Depends(get_db),
):
    """Send broadcast message to filtered leads."""
    company_result = await db.execute(select(Company).where(Company.id == company_id))
    company = company_result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")

    result = await db.execute(_build_leads_query(company_id, data))
    leads = result.scalars().all()

    sent, failed = await _send_to_leads(db, leads, data.message, company)

    return {
        "total_targeted": len(leads),
        "sent": sent,
        "failed": failed,
        "message": data.message[:100],
    }


async def _send_to_leads(
    db: AsyncSession,
    leads: list[Lead],
    message: str,
    company: Company,
) -> tuple[int, int]:
    """Send message to each lead. Returns (sent, failed) counts."""
    sent = 0
    failed = 0

    for lead in leads:
        conv_result = await db.execute(
            select(Conversation).where(
                Conversation.lead_id == lead.id,
                Conversation.company_id == company.id,
                Conversation.status.in_(["active", "handed_off"]),
            ).limit(1)
        )
        conv = conv_result.scalar_one_or_none()
        if not conv:
            continue

        msg = Message(
            conversation_id=conv.id,
            direction="outbound",
            sender_type="human",
            msg_type="text",
            content=message,
        )
        db.add(msg)

        if lead.whatsapp_id and company.whatsapp_token:
            try:
                await send_text_message(
                    company.phone_number_id or "",
                    lead.whatsapp_id,
                    message,
                )
                sent += 1
            except Exception:
                logger.warning("Failed to send broadcast to lead %s", lead.id)
                failed += 1
        else:
            sent += 1

    await db.flush()
    return sent, failed
