"""Follow-up management API — DB-backed."""

import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import get_current_company_id
from app.services.follow_up_engine import (
    DEFAULT_SEQUENCES,
    cancel_followups_for_lead,
    get_all_followups_for_company,
    schedule_followup,
)

router = APIRouter()


@router.get("/sequences")
async def list_sequences(company_id: uuid.UUID = Depends(get_current_company_id)):
    return {
        key: {
            "name": seq["name"],
            "description": seq["description"],
            "trigger_stage": seq["trigger_stage"],
            "steps_count": len(seq["steps"]),
            "steps": seq["steps"],
        }
        for key, seq in DEFAULT_SEQUENCES.items()
    }


@router.get("/pending")
async def list_pending(
    company_id: uuid.UUID = Depends(get_current_company_id),
    db: AsyncSession = Depends(get_db),
):
    return await get_all_followups_for_company(db, company_id)


class ScheduleRequest(BaseModel):
    lead_id: str
    conversation_id: str
    sequence_key: str


@router.post("/schedule")
async def schedule(
    data: ScheduleRequest,
    company_id: uuid.UUID = Depends(get_current_company_id),
    db: AsyncSession = Depends(get_db),
):
    result = await schedule_followup(
        db=db,
        lead_id=uuid.UUID(data.lead_id),
        company_id=company_id,
        conversation_id=uuid.UUID(data.conversation_id),
        sequence_key=data.sequence_key,
    )
    if not result:
        return {"error": "Secuencia no encontrada o sin pasos"}
    return {"id": str(result.id), "status": "scheduled", "scheduled_at": result.scheduled_at.isoformat()}


@router.post("/cancel/{lead_id}")
async def cancel(
    lead_id: uuid.UUID,
    company_id: uuid.UUID = Depends(get_current_company_id),
    db: AsyncSession = Depends(get_db),
):
    cancelled = await cancel_followups_for_lead(db, lead_id)
    return {"cancelled": cancelled}
