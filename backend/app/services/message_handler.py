"""Central message handler — coordinates the flow from inbound message to AI response."""

import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import Company
from app.models.conversation import Conversation
from app.models.lead import Lead
from app.models.message import Message
from app.services.ai_agent import generate_response
from app.services.lead_scorer import extract_signals_from_message, update_score
from app.services.whatsapp_client import send_text_message

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

    # 1. Find company by phone_number_id
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
        channel_ts=datetime.fromtimestamp(int(timestamp), tz=timezone.utc) if timestamp else None,
    )
    db.add(inbound_msg)

    # Update lead last_message_at
    lead.last_message_at = datetime.now(timezone.utc)
    await db.flush()

    # 4b. Cancel pending follow-ups (lead responded)
    try:
        from app.services.follow_up_engine import cancel_followups_for_lead
        await cancel_followups_for_lead(str(lead.id))
    except Exception:
        pass

    # 4c. Score the lead based on message content
    if content:
        signals = extract_signals_from_message(content)
        if signals:
            scoring_rules = company.scoring_rules if hasattr(company, "scoring_rules") else None
            new_score = await update_score(db, lead, signals, scoring_rules)

            # 4d. Alert seller if lead is hot (score >= 76)
            if new_score >= 76:
                try:
                    from app.tasks.notifications import alert_hot_lead
                    alert_hot_lead.delay(str(lead.id), str(company.id), new_score, lead.name)
                except Exception:
                    logger.warning("Failed to queue hot lead alert (Celery not running?)")

    # 5. Generate AI response if enabled
    if not conversation.ai_enabled:
        logger.info("AI disabled for conversation %s, skipping", conversation.id)
        return

    # Build conversation history from recent messages
    history = await _build_conversation_history(db, conversation.id)

    # 6. Call AI agent
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

    # 7. Send response via channel (skip in development if no real token)
    if channel == "whatsapp" and phone_number_id:
        from app.config import settings as _settings
        if _settings.whatsapp_access_token:
            try:
                await send_text_message(phone_number_id, sender_id, response_text)
            except Exception:
                logger.warning("Failed to send WhatsApp message (dev mode?)")
        else:
            logger.info("Skipping WhatsApp send (no access token configured)")

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

    # Update lead response time
    lead.last_response_at = datetime.now(timezone.utc)
    await db.flush()

    logger.info(
        "Processed message for lead=%s, tools=%s, tokens=%d+%d",
        lead.id,
        ai_result.get("tools_used"),
        ai_result.get("tokens_in", 0),
        ai_result.get("tokens_out", 0),
    )

    # 9. Notify SSE listeners
    try:
        from app.api.conversations import _notify
        _notify(str(company.id), {
            "type": "new_message",
            "conversation_id": str(conversation.id),
            "lead_name": lead.name,
            "message": {
                "direction": "inbound",
                "sender_type": "lead",
                "content": content[:100],
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
        })
        if response_text:
            _notify(str(company.id), {
                "type": "new_message",
                "conversation_id": str(conversation.id),
                "message": {
                    "direction": "outbound",
                    "sender_type": "ai",
                    "content": response_text[:100],
                    "created_at": datetime.now(timezone.utc).isoformat(),
                },
            })
    except Exception:
        pass  # SSE notification is best-effort


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
