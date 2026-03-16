"""Follow-up engine — manages automated follow-up sequences."""

import logging
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lead import Lead
from app.models.conversation import Conversation

logger = logging.getLogger(__name__)

# Default follow-up sequences (configurable per company)
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
        "description": "Secuencia para leads que pidieron precio",
        "trigger_stage": "interested",
        "steps": [
            {"delay_hours": 4, "type": "reminder", "message": "Espero que la informacion te haya sido util! Si tenes alguna duda sobre el presupuesto, estoy para ayudarte."},
            {"delay_hours": 48, "type": "check_in", "message": "Hola! Queria saber si pudiste evaluar la cotizacion. Te gustaria agendar una visita para ver los modelos?"},
        ],
    },
    "post_visita": {
        "name": "Post Visita",
        "description": "Secuencia despues de una visita al showroom",
        "trigger_stage": "visiting",
        "steps": [
            {"delay_hours": 2, "type": "reminder", "message": "Gracias por visitarnos! Espero que te haya gustado lo que viste. Alguna consulta adicional?"},
            {"delay_hours": 48, "type": "check_in", "message": "Hola! Queria saber si ya pudiste decidir. Recorda que podemos ofrecer financiacion a medida."},
            {"delay_hours": 168, "type": "offer", "message": "Hola! Seguimos con disponibilidad del modelo que te gusto. Te gustaria avanzar? 🏠"},
        ],
    },
    "reactivacion": {
        "name": "Reactivacion",
        "description": "Para leads que no respondieron en 7+ dias",
        "trigger_stage": None,
        "steps": [
            {"delay_hours": 0, "type": "reactivation", "message": "Hola! Hace un tiempo nos consultaste sobre nuestros productos. Tenemos novedades que te pueden interesar!"},
        ],
    },
}


# In-memory follow-up store (will be replaced with DB table + Celery in production)
_pending_followups: list[dict] = []


async def schedule_followup(
    db: AsyncSession,
    lead_id: uuid.UUID,
    company_id: uuid.UUID,
    conversation_id: uuid.UUID,
    sequence_key: str,
    step_index: int = 0,
) -> dict | None:
    """Schedule the next follow-up step for a lead."""
    sequence = DEFAULT_SEQUENCES.get(sequence_key)
    if not sequence or step_index >= len(sequence["steps"]):
        return None

    step = sequence["steps"][step_index]
    scheduled_at = datetime.now(timezone.utc) + timedelta(hours=step["delay_hours"])

    followup = {
        "id": str(uuid.uuid4()),
        "lead_id": str(lead_id),
        "company_id": str(company_id),
        "conversation_id": str(conversation_id),
        "sequence_key": sequence_key,
        "step_index": step_index,
        "type": step["type"],
        "message": step["message"],
        "scheduled_at": scheduled_at.isoformat(),
        "status": "pending",
    }

    _pending_followups.append(followup)
    logger.info("Follow-up scheduled: lead=%s, sequence=%s, step=%d, at=%s", lead_id, sequence_key, step_index, scheduled_at)
    return followup


async def get_pending_followups(company_id: str | None = None) -> list[dict]:
    """Get all pending follow-ups, optionally filtered by company."""
    now = datetime.now(timezone.utc).isoformat()
    pending = [
        f for f in _pending_followups
        if f["status"] == "pending" and f["scheduled_at"] <= now
    ]
    if company_id:
        pending = [f for f in pending if f["company_id"] == company_id]
    return pending


async def cancel_followups_for_lead(lead_id: str) -> int:
    """Cancel all pending follow-ups for a lead (e.g., when lead responds)."""
    cancelled = 0
    for f in _pending_followups:
        if f["lead_id"] == lead_id and f["status"] == "pending":
            f["status"] = "cancelled"
            f["skip_reason"] = "lead_responded"
            cancelled += 1
    if cancelled:
        logger.info("Cancelled %d follow-ups for lead %s (lead responded)", cancelled, lead_id)
    return cancelled


async def execute_followup(followup: dict, db: AsyncSession) -> bool:
    """Execute a single follow-up — send the message."""
    from app.services.message_handler import _find_or_create_conversation
    from app.models.message import Message
    from app.models.company import Company

    lead_id = uuid.UUID(followup["lead_id"])
    company_id = uuid.UUID(followup["company_id"])

    # Get lead
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()
    if not lead:
        followup["status"] = "skipped"
        followup["skip_reason"] = "lead_not_found"
        return False

    # Check if lead already responded (cancel remaining follow-ups)
    if lead.last_message_at:
        scheduled = datetime.fromisoformat(followup["scheduled_at"])
        if lead.last_message_at > scheduled - timedelta(hours=1):
            followup["status"] = "skipped"
            followup["skip_reason"] = "lead_already_responded"
            return False

    # Get conversation
    conv_id = uuid.UUID(followup["conversation_id"])
    conv_result = await db.execute(select(Conversation).where(Conversation.id == conv_id))
    conversation = conv_result.scalar_one_or_none()
    if not conversation:
        followup["status"] = "skipped"
        followup["skip_reason"] = "conversation_not_found"
        return False

    # Save follow-up message
    msg = Message(
        conversation_id=conversation.id,
        direction="outbound",
        sender_type="ai",
        msg_type="text",
        content=followup["message"],
    )
    db.add(msg)

    # Send via WhatsApp if configured
    if conversation.channel == "whatsapp" and lead.whatsapp_id:
        company_result = await db.execute(select(Company).where(Company.id == company_id))
        company = company_result.scalar_one_or_none()
        if company and company.whatsapp_token:
            try:
                from app.services.whatsapp_client import send_text_message
                await send_text_message(company.phone_number_id or "", lead.whatsapp_id, followup["message"])
            except Exception:
                logger.warning("Failed to send follow-up via WhatsApp for lead %s", lead_id)

    await db.flush()

    followup["status"] = "sent"
    followup["executed_at"] = datetime.now(timezone.utc).isoformat()

    # Schedule next step
    next_step = followup["step_index"] + 1
    await schedule_followup(db, lead_id, company_id, conv_id, followup["sequence_key"], next_step)

    logger.info("Follow-up executed: lead=%s, sequence=%s, step=%d", lead_id, followup["sequence_key"], followup["step_index"])
    return True


def get_all_followups() -> list[dict]:
    """Get all follow-ups (for dashboard)."""
    return list(_pending_followups)
