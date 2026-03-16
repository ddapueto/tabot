"""Follow-up management API."""

import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.follow_up_engine import (
    DEFAULT_SEQUENCES,
    cancel_followups_for_lead,
    get_all_followups,
    schedule_followup,
)

router = APIRouter()


@router.get("/{company_id}/sequences")
async def list_sequences(company_id: uuid.UUID):
    """List available follow-up sequences."""
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


@router.get("/{company_id}/pending")
async def list_pending(company_id: uuid.UUID):
    """List all follow-ups (pending, sent, cancelled)."""
    all_followups = get_all_followups()
    company_followups = [f for f in all_followups if f["company_id"] == str(company_id)]
    return company_followups


class ScheduleRequest(BaseModel):
    lead_id: str
    conversation_id: str
    sequence_key: str


@router.post("/{company_id}/schedule")
async def schedule(
    company_id: uuid.UUID,
    data: ScheduleRequest,
    db: AsyncSession = Depends(get_db),
):
    """Manually schedule a follow-up sequence for a lead."""
    result = await schedule_followup(
        db=db,
        lead_id=uuid.UUID(data.lead_id),
        company_id=company_id,
        conversation_id=uuid.UUID(data.conversation_id),
        sequence_key=data.sequence_key,
    )
    if not result:
        return {"error": "Secuencia no encontrada o sin pasos"}
    return result


@router.post("/{company_id}/cancel/{lead_id}")
async def cancel(company_id: uuid.UUID, lead_id: uuid.UUID):
    """Cancel all pending follow-ups for a lead."""
    cancelled = await cancel_followups_for_lead(str(lead_id))
    return {"cancelled": cancelled}
