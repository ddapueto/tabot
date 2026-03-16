import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from pydantic import BaseModel

from app.database import get_db
from app.models.lead import Lead
from app.models.conversation import Conversation
from app.schemas.lead import LeadResponse, LeadUpdate
from app.services.lead_scorer import change_stage, VALID_STAGES

router = APIRouter()


@router.get("/{company_id}", response_model=list[LeadResponse])
async def list_leads(
    company_id: uuid.UUID,
    stage: str | None = None,
    priority: str | None = None,
    channel: str | None = None,
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    query = select(Lead).where(Lead.company_id == company_id)
    if stage:
        query = query.where(Lead.stage == stage)
    if priority:
        query = query.where(Lead.priority == priority)
    if channel:
        query = query.where(Lead.source_channel == channel)
    query = query.order_by(Lead.score.desc(), Lead.last_message_at.desc())
    query = query.limit(limit).offset(offset)

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{company_id}/{lead_id}", response_model=LeadResponse)
async def get_lead(
    company_id: uuid.UUID,
    lead_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Lead).where(Lead.id == lead_id, Lead.company_id == company_id)
    )
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead no encontrado")
    return lead


@router.patch("/{company_id}/{lead_id}", response_model=LeadResponse)
async def update_lead(
    company_id: uuid.UUID,
    lead_id: uuid.UUID,
    data: LeadUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Lead).where(Lead.id == lead_id, Lead.company_id == company_id)
    )
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead no encontrado")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(lead, field, value)

    await db.flush()
    await db.refresh(lead)
    return lead


class StageChangeRequest(BaseModel):
    stage: str
    reason: str | None = None


@router.post("/{company_id}/{lead_id}/stage", response_model=LeadResponse)
async def change_lead_stage(
    company_id: uuid.UUID,
    lead_id: uuid.UUID,
    data: StageChangeRequest,
    db: AsyncSession = Depends(get_db),
):
    """Change lead stage with validation."""
    if data.stage not in VALID_STAGES:
        raise HTTPException(status_code=400, detail=f"Stage invalido. Validos: {VALID_STAGES}")

    result = await db.execute(
        select(Lead).where(Lead.id == lead_id, Lead.company_id == company_id)
    )
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead no encontrado")

    success = await change_stage(db, lead, data.stage, changed_by="user", reason=data.reason)
    if not success:
        raise HTTPException(status_code=400, detail=f"Transicion invalida: {lead.stage} → {data.stage}")

    await db.refresh(lead)
    return lead


class HandoffRequest(BaseModel):
    reason: str
    urgency: str = "normal"


@router.post("/{company_id}/{lead_id}/handoff")
async def handoff_to_human(
    company_id: uuid.UUID,
    lead_id: uuid.UUID,
    data: HandoffRequest,
    db: AsyncSession = Depends(get_db),
):
    """Handoff conversation to human — pauses AI, notifies seller."""
    result = await db.execute(
        select(Lead).where(Lead.id == lead_id, Lead.company_id == company_id)
    )
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead no encontrado")

    # Pause AI on active conversations
    conv_result = await db.execute(
        select(Conversation).where(
            Conversation.lead_id == lead_id,
            Conversation.company_id == company_id,
            Conversation.status == "active",
        )
    )
    conversations = conv_result.scalars().all()
    for conv in conversations:
        conv.ai_enabled = False
        conv.status = "handed_off"

    await db.flush()

    return {
        "status": "handed_off",
        "lead_id": str(lead_id),
        "conversations_paused": len(conversations),
        "reason": data.reason,
    }


@router.post("/{company_id}/{lead_id}/reactivate-ai")
async def reactivate_ai(
    company_id: uuid.UUID,
    lead_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Re-enable AI on conversations for this lead."""
    conv_result = await db.execute(
        select(Conversation).where(
            Conversation.lead_id == lead_id,
            Conversation.company_id == company_id,
        )
    )
    conversations = conv_result.scalars().all()
    reactivated = 0
    for conv in conversations:
        if not conv.ai_enabled:
            conv.ai_enabled = True
            conv.status = "active"
            reactivated += 1

    await db.flush()
    return {"status": "ai_reactivated", "conversations_reactivated": reactivated}
