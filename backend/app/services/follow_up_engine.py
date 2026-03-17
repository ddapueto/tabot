"""Follow-up engine — manages automated follow-up sequences in DB."""

import logging
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.follow_up import FollowUp
from app.models.lead import Lead
from app.models.conversation import Conversation
from app.models.message import Message

logger = logging.getLogger(__name__)

DEFAULT_SEQUENCES = {
    "nuevo_lead": {
        "name": "Nuevo Lead",
        "description": "Secuencia para leads que no respondieron",
        "trigger_stage": "new",
        "steps": [
            {"delay_hours": 2, "type": "reminder", "message": "Hola! Vi que nos escribiste hace un rato. Queres que te cuente mas sobre nuestros productos? 😊"},
            {"delay_hours": 24, "type": "check_in", "message": "Buen dia! Seguimos a tu disposicion si tenes alguna consulta. Te puedo mostrar nuestro catalogo completo."},
            {"delay_hours": 72, "type": "offer", "message": "Hola! Te comparto que esta semana tenemos promociones especiales. Te gustaria que te cuente?"},
        ],
    },
    "post_consulta": {
        "name": "Post Consulta de Precio",
        "description": "Para leads que pidieron precio",
        "trigger_stage": "interested",
        "steps": [
            {"delay_hours": 4, "type": "reminder", "message": "Espero que la informacion te haya sido util! Si tenes alguna duda sobre el presupuesto, estoy para ayudarte."},
            {"delay_hours": 48, "type": "check_in", "message": "Hola! Queria saber si pudiste evaluar la cotizacion. Te gustaria agendar una visita para ver los modelos?"},
        ],
    },
    "post_visita": {
        "name": "Post Visita",
        "description": "Despues de una visita al showroom",
        "trigger_stage": "visiting",
        "steps": [
            {"delay_hours": 2, "type": "reminder", "message": "Gracias por visitarnos! Espero que te haya gustado lo que viste. Alguna consulta adicional?"},
            {"delay_hours": 48, "type": "check_in", "message": "Hola! Queria saber si ya pudiste decidir. Recorda que podemos ofrecer financiacion a medida."},
            {"delay_hours": 168, "type": "offer", "message": "Hola! Seguimos con disponibilidad del modelo que te gusto. Te gustaria avanzar? 🏠"},
        ],
    },
    "reactivacion": {
        "name": "Reactivacion",
        "description": "Para leads sin respuesta en 7+ dias",
        "trigger_stage": None,
        "steps": [
            {"delay_hours": 0, "type": "reactivation", "message": "Hola! Hace un tiempo nos consultaste sobre nuestros productos. Tenemos novedades que te pueden interesar!"},
        ],
    },
}


async def schedule_followup(
    db: AsyncSession,
    lead_id: uuid.UUID,
    company_id: uuid.UUID,
    conversation_id: uuid.UUID,
    sequence_key: str,
    step_index: int = 0,
) -> FollowUp | None:
    """Schedule the next follow-up step in DB."""
    sequence = DEFAULT_SEQUENCES.get(sequence_key)
    if not sequence or step_index >= len(sequence["steps"]):
        return None

    step = sequence["steps"][step_index]
    scheduled_at = datetime.now(timezone.utc) + timedelta(hours=step["delay_hours"])

    followup = FollowUp(
        lead_id=lead_id,
        company_id=company_id,
        conversation_id=conversation_id,
        sequence_key=sequence_key,
        step_index=step_index,
        type=step["type"],
        message=step["message"],
        scheduled_at=scheduled_at,
        status="pending",
    )
    db.add(followup)
    await db.flush()

    logger.info("Follow-up scheduled: lead=%s, seq=%s, step=%d, at=%s", lead_id, sequence_key, step_index, scheduled_at)
    return followup


async def get_pending_followups(db: AsyncSession, company_id: uuid.UUID | None = None) -> list[FollowUp]:
    """Get pending follow-ups that are due."""
    now = datetime.now(timezone.utc)
    query = (
        select(FollowUp)
        .where(FollowUp.status == "pending", FollowUp.scheduled_at <= now)
        .order_by(FollowUp.scheduled_at)
        .limit(50)
    )
    if company_id:
        query = query.where(FollowUp.company_id == company_id)

    result = await db.execute(query)
    return list(result.scalars().all())


async def get_all_followups_for_company(db: AsyncSession, company_id: uuid.UUID) -> list[dict]:
    """Get all follow-ups for a company (for dashboard)."""
    result = await db.execute(
        select(FollowUp)
        .where(FollowUp.company_id == company_id)
        .order_by(FollowUp.scheduled_at.desc())
        .limit(100)
    )
    return [
        {
            "id": str(f.id),
            "lead_id": str(f.lead_id),
            "sequence_key": f.sequence_key,
            "step_index": f.step_index,
            "type": f.type,
            "message": f.message[:100],
            "scheduled_at": f.scheduled_at.isoformat(),
            "executed_at": f.executed_at.isoformat() if f.executed_at else None,
            "status": f.status,
            "skip_reason": f.skip_reason,
        }
        for f in result.scalars().all()
    ]


async def cancel_followups_for_lead(db: AsyncSession, lead_id: uuid.UUID) -> int:
    """Cancel all pending follow-ups for a lead (e.g. when lead responds)."""
    result = await db.execute(
        update(FollowUp)
        .where(FollowUp.lead_id == lead_id, FollowUp.status == "pending")
        .values(status="cancelled", skip_reason="lead_responded")
        .returning(FollowUp.id)
    )
    cancelled_ids = result.scalars().all()
    if cancelled_ids:
        logger.info("Cancelled %d follow-ups for lead %s", len(cancelled_ids), lead_id)
    return len(cancelled_ids)


async def execute_followup(followup: FollowUp, db: AsyncSession) -> bool:
    """Execute a single follow-up — send the message and schedule next step."""
    from app.models.company import Company

    # Get lead
    result = await db.execute(select(Lead).where(Lead.id == followup.lead_id))
    lead = result.scalar_one_or_none()
    if not lead:
        followup.status = "skipped"
        followup.skip_reason = "lead_not_found"
        return False

    # Check if lead responded since scheduling
    if lead.last_message_at and lead.last_message_at > followup.created_at:
        followup.status = "skipped"
        followup.skip_reason = "lead_responded_after_schedule"
        return False

    # Get conversation
    if followup.conversation_id:
        conv_result = await db.execute(select(Conversation).where(Conversation.id == followup.conversation_id))
        conversation = conv_result.scalar_one_or_none()
    else:
        conversation = None

    if not conversation:
        followup.status = "skipped"
        followup.skip_reason = "conversation_not_found"
        return False

    # Save follow-up message
    msg = Message(
        conversation_id=conversation.id,
        direction="outbound",
        sender_type="ai",
        msg_type="text",
        content=followup.message,
    )
    db.add(msg)

    # Send via WhatsApp if configured
    if conversation.channel == "whatsapp" and lead.whatsapp_id:
        company_result = await db.execute(select(Company).where(Company.id == followup.company_id))
        company = company_result.scalar_one_or_none()
        if company and company.whatsapp_token:
            try:
                from app.services.whatsapp_client import send_text_message
                await send_text_message(company.phone_number_id or "", lead.whatsapp_id, followup.message)
            except Exception:
                logger.warning("Failed to send follow-up via WhatsApp for lead %s", followup.lead_id)

    followup.status = "sent"
    followup.executed_at = datetime.now(timezone.utc)
    await db.flush()

    # Schedule next step
    next_step = followup.step_index + 1
    await schedule_followup(
        db, followup.lead_id, followup.company_id,
        followup.conversation_id, followup.sequence_key, next_step,
    )

    logger.info("Follow-up executed: lead=%s, seq=%s, step=%d", followup.lead_id, followup.sequence_key, followup.step_index)
    return True
