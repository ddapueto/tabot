import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.lead import Lead
from app.schemas.lead import LeadResponse, LeadUpdate

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
