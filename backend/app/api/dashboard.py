"""Dashboard endpoints — aggregated stats."""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import func, select, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.lead import Lead
from app.models.conversation import Conversation
from app.models.message import Message
from app.api.deps import get_current_company_id

router = APIRouter()


@router.get("/stats")
async def get_dashboard_stats(
    company_id: uuid.UUID = Depends(get_current_company_id),
    db: AsyncSession = Depends(get_db),
):
    total_leads = await db.execute(
        select(func.count(Lead.id)).where(Lead.company_id == company_id)
    )
    stages = await db.execute(
        select(Lead.stage, func.count(Lead.id))
        .where(Lead.company_id == company_id).group_by(Lead.stage)
    )
    total_convs = await db.execute(
        select(func.count(Conversation.id)).where(Conversation.company_id == company_id)
    )
    msg_stats = await db.execute(
        select(
            func.count(Message.id).label("total"),
            func.count(case((Message.direction == "inbound", 1))).label("inbound"),
            func.count(case((Message.direction == "outbound", 1))).label("outbound"),
            func.count(case((Message.sender_type == "ai", 1))).label("ai_responses"),
        )
        .join(Conversation, Message.conversation_id == Conversation.id)
        .where(Conversation.company_id == company_id)
    )
    msg_row = msg_stats.one()
    priorities = await db.execute(
        select(Lead.priority, func.count(Lead.id))
        .where(Lead.company_id == company_id).group_by(Lead.priority)
    )
    channels = await db.execute(
        select(Lead.source_channel, func.count(Lead.id))
        .where(Lead.company_id == company_id, Lead.source_channel.is_not(None))
        .group_by(Lead.source_channel)
    )

    return {
        "total_leads": total_leads.scalar() or 0,
        "total_conversations": total_convs.scalar() or 0,
        "messages": {"total": msg_row.total, "inbound": msg_row.inbound, "outbound": msg_row.outbound, "ai_responses": msg_row.ai_responses},
        "leads_by_stage": dict(stages.all()),
        "leads_by_priority": dict(priorities.all()),
        "leads_by_channel": dict(channels.all()),
    }


@router.get("/recent-leads")
async def get_recent_leads(
    company_id: uuid.UUID = Depends(get_current_company_id),
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Lead).where(Lead.company_id == company_id)
        .order_by(Lead.created_at.desc()).limit(limit)
    )
    return [
        {
            "id": str(l.id), "name": l.name, "score": l.score, "stage": l.stage,
            "priority": l.priority, "source_channel": l.source_channel,
            "last_message_at": l.last_message_at.isoformat() if l.last_message_at else None,
            "created_at": l.created_at.isoformat(),
        }
        for l in result.scalars().all()
    ]
