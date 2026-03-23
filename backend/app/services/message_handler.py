"""Central message handler — coordinates the flow from inbound message to AI response."""

import logging
import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings as app_settings
from app.models.company import Company
from app.models.conversation import Conversation
from app.models.lead import Lead
from app.models.message import Message
from app.services.ai_agent import generate_response
from app.services.follow_up_engine import cancel_followups_for_lead
from app.services.lead_scorer import extract_signals_from_message, update_score
from app.services.response_validator import validate_response
from app.services.sse import notify
from app.services.whatsapp_client import send_text_message
from app.tasks.notifications import alert_hot_lead

logger = logging.getLogger(__name__)


async def handle_inbound_message(
    db: AsyncSession,
    channel: str,
    phone_number_id: str | None,
    sender_id: str,
    sender_name: str | None,
    msg_type: str,
    content: str,
    channel_msg_id: str | None = None,
    timestamp: str | None = None,
    raw_payload: dict | None = None,
) -> None:
    """Process an inbound message from any channel."""

    # 1. Find company
    company = await _find_company(db, channel, phone_number_id)
    if not company:
        logger.warning("No company found for phone_number_id=%s", phone_number_id)
        return

    # 2. Find or create lead
    lead = await _find_or_create_lead(db, company.id, channel, sender_id, sender_name)

    # 3. Find or create active conversation
    conversation = await _find_or_create_conversation(db, lead.id, company.id, channel)

    # 4. Save inbound message
    inbound_msg = Message(
        conversation_id=conversation.id,
        direction="inbound",
        sender_type="lead",
        sender_id=sender_id,
        msg_type=msg_type,
        content=content,
        channel_msg_id=channel_msg_id,
        channel_ts=datetime.fromtimestamp(int(timestamp), tz=UTC) if timestamp else None,
    )
    db.add(inbound_msg)
    lead.last_message_at = datetime.now(UTC)
    await db.flush()

    # 5. Score lead and handle follow-ups
    await _score_and_alert(db, lead, company, content)

    # 6. Generate AI response if enabled
    if not conversation.ai_enabled:
        logger.info("AI disabled for conversation %s, skipping", conversation.id)
        return

    history = await _build_conversation_history(db, conversation.id)
    ai_result = await generate_response(
        company=company,
        lead=lead,
        conversation_history=history,
        db=db,
        company_id=company.id,
    )

    response_text = ai_result["text"]
    if not response_text:
        return

    # 7. Validate and send response
    response_text = await _validate_and_send(
        db, company, conversation, lead, response_text, channel, phone_number_id, sender_id,
    )

    # 8. Save outbound message
    outbound_msg = Message(
        conversation_id=conversation.id,
        direction="outbound",
        sender_type="ai",
        msg_type="text",
        content=response_text,
        ai_model=ai_result.get("model"),
        ai_tokens_in=ai_result.get("tokens_in"),
        ai_tokens_out=ai_result.get("tokens_out"),
        ai_tools_used=ai_result.get("tools_used"),
    )
    db.add(outbound_msg)
    lead.last_response_at = datetime.now(UTC)
    await db.flush()

    logger.info(
        "Processed message for lead=%s, tools=%s, tokens=%d+%d",
        lead.id,
        ai_result.get("tools_used"),
        ai_result.get("tokens_in", 0),
        ai_result.get("tokens_out", 0),
    )

    # 9. Notify SSE listeners
    _notify_sse(str(company.id), str(conversation.id), lead.name, content, response_text)


async def _score_and_alert(
    db: AsyncSession,
    lead: Lead,
    company: Company,
    content: str,
) -> None:
    """Cancel pending follow-ups, score the lead, and alert if hot."""
    try:
        await cancel_followups_for_lead(db, lead.id)
    except Exception:
        logger.debug("Could not cancel follow-ups for lead %s", lead.id)

    if not content:
        return

    signals = extract_signals_from_message(content)
    if not signals:
        return

    scoring_rules = company.scoring_rules if hasattr(company, "scoring_rules") else None
    new_score = await update_score(db, lead, signals, scoring_rules)

    if new_score >= 76:
        try:
            alert_hot_lead.delay(str(lead.id), str(company.id), new_score, lead.name)
        except Exception:
            logger.warning("Failed to queue hot lead alert (Celery not running?)")


async def _validate_and_send(
    db: AsyncSession,
    company: Company,
    conversation: Conversation,
    lead: Lead,
    response_text: str,
    channel: str,
    phone_number_id: str | None,
    sender_id: str,
) -> str:
    """Validate AI response and send via channel. Returns final response text."""
    validation = await validate_response(db, company.id, response_text)

    if validation["should_escalate"]:
        logger.warning("AI response blocked for lead %s: %s", lead.id, validation["issues"])
        response_text = (
            "Voy a consultar esto con el equipo para darte una respuesta precisa. "
            "Un vendedor te va a responder pronto."
        )
        conversation.ai_enabled = False
        conversation.status = "handed_off"
        await db.flush()
    elif validation["corrected_response"] != response_text:
        logger.info(
            "AI response corrected for lead %s: %s",
            lead.id,
            [i for i in validation["issues"] if i["type"] == "price_corrected"],
        )
        response_text = validation["corrected_response"]

    if channel == "whatsapp" and phone_number_id:
        if app_settings.whatsapp_access_token:
            try:
                await send_text_message(phone_number_id, sender_id, response_text)
            except Exception:
                logger.warning("Failed to send WhatsApp message to %s", sender_id)
        else:
            logger.info("Skipping WhatsApp send (no access token configured)")

    return response_text


def _notify_sse(
    company_id: str,
    conversation_id: str,
    lead_name: str | None,
    inbound_content: str,
    response_text: str,
) -> None:
    """Notify SSE listeners about new inbound + outbound messages."""
    now = datetime.now(UTC).isoformat()
    try:
        notify(company_id, {
            "type": "new_message",
            "conversation_id": conversation_id,
            "lead_name": lead_name,
            "message": {
                "direction": "inbound",
                "sender_type": "lead",
                "content": inbound_content[:100],
                "created_at": now,
            },
        })
        if response_text:
            notify(company_id, {
                "type": "new_message",
                "conversation_id": conversation_id,
                "message": {
                    "direction": "outbound",
                    "sender_type": "ai",
                    "content": response_text[:100],
                    "created_at": now,
                },
            })
    except Exception:
        logger.debug("SSE notification failed (best-effort)")


async def _find_company(
    db: AsyncSession, channel: str, phone_number_id: str | None
) -> Company | None:
    """Find company by channel identifier."""
    if channel == "whatsapp" and phone_number_id:
        result = await db.execute(
            select(Company).where(Company.phone_number_id == phone_number_id)
        )
        return result.scalar_one_or_none()
    return None


async def _find_or_create_lead(
    db: AsyncSession,
    company_id: uuid.UUID,
    channel: str,
    sender_id: str,
    sender_name: str | None,
) -> Lead:
    """Find existing lead or create new one."""
    if channel == "whatsapp":
        result = await db.execute(
            select(Lead).where(
                Lead.company_id == company_id,
                Lead.whatsapp_id == sender_id,
            )
        )
        lead = result.scalar_one_or_none()
        if lead:
            if sender_name and not lead.name:
                lead.name = sender_name
            return lead

        lead = Lead(
            company_id=company_id,
            whatsapp_id=sender_id,
            whatsapp_phone=sender_id,
            name=sender_name,
            source_channel="whatsapp",
            stage="new",
            score=0,
        )
        db.add(lead)
        await db.flush()
        return lead

    elif channel in ("instagram_dm", "instagram_comment"):
        result = await db.execute(
            select(Lead).where(
                Lead.company_id == company_id,
                Lead.instagram_id == sender_id,
            )
        )
        lead = result.scalar_one_or_none()
        if lead:
            return lead

        lead = Lead(
            company_id=company_id,
            instagram_id=sender_id,
            instagram_username=sender_name,
            name=sender_name,
            source_channel=channel,
            stage="new",
            score=0,
        )
        db.add(lead)
        await db.flush()
        return lead

    raise ValueError(f"Unsupported channel: {channel}")


async def _find_or_create_conversation(
    db: AsyncSession,
    lead_id: uuid.UUID,
    company_id: uuid.UUID,
    channel: str,
) -> Conversation:
    """Find active conversation or create new one."""
    result = await db.execute(
        select(Conversation).where(
            Conversation.lead_id == lead_id,
            Conversation.company_id == company_id,
            Conversation.channel == channel,
            Conversation.status == "active",
        )
    )
    conversation = result.scalar_one_or_none()
    if conversation:
        return conversation

    conversation = Conversation(
        lead_id=lead_id,
        company_id=company_id,
        channel=channel,
        status="active",
        ai_enabled=True,
    )
    db.add(conversation)
    await db.flush()
    return conversation


async def _build_conversation_history(
    db: AsyncSession, conversation_id: uuid.UUID, limit: int = 20
) -> list[dict]:
    """Build conversation history for Claude API format."""
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.desc())
        .limit(limit)
    )
    messages = list(reversed(result.scalars().all()))

    history = []
    for msg in messages:
        if not msg.content:
            continue
        role = "user" if msg.direction == "inbound" else "assistant"
        history.append({"role": role, "content": msg.content})

    return history
