"""Instagram webhook handler — DMs, comments, and content capture."""

import hashlib
import hmac
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.company import Company
from app.models.knowledge import KnowledgeItem
from app.services.message_handler import handle_inbound_message

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/instagram")
async def verify_webhook(
    hub_mode: str = Query(alias="hub.mode", default=""),
    hub_verify_token: str = Query(alias="hub.verify_token", default=""),
    hub_challenge: str = Query(alias="hub.challenge", default=""),
):
    """Meta webhook verification for Instagram."""
    if hub_mode == "subscribe" and hub_verify_token == settings.meta_verify_token:
        return int(hub_challenge)
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/instagram")
async def receive_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """Receive Instagram DMs, comments, and content updates."""
    body = await request.body()

    # Verify signature
    signature = request.headers.get("X-Hub-Signature-256", "")
    if settings.meta_app_secret:
        expected = hmac.new(settings.meta_app_secret.encode(), body, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(f"sha256={expected}", signature):
            raise HTTPException(status_code=403, detail="Invalid signature")

    payload = await request.json()

    for entry in payload.get("entry", []):
        # Handle DMs (messaging)
        for messaging in entry.get("messaging", []):
            await _handle_dm(db, messaging)

        # Handle content changes (comments, new posts)
        for change in entry.get("changes", []):
            field = change.get("field")
            value = change.get("value", {})

            if field == "comments":
                await _handle_comment(db, value, entry.get("id"))
            elif field == "feed":
                await _handle_content(db, value, entry.get("id"))

    return {"status": "ok"}


async def _handle_dm(db: AsyncSession, messaging: dict):
    """Process an Instagram DM."""
    sender_id = messaging.get("sender", {}).get("id", "")
    recipient_id = messaging.get("recipient", {}).get("id", "")
    message = messaging.get("message", {})

    if not sender_id or sender_id == recipient_id:
        return  # Skip echo messages

    # Find company by IG account ID
    company = await _find_company_by_ig(db, recipient_id)
    if not company:
        logger.warning("No company found for IG account %s", recipient_id)
        return

    content = message.get("text", "")
    msg_type = "text"

    # Handle media messages
    attachments = message.get("attachments", [])
    if attachments:
        msg_type = attachments[0].get("type", "image")
        if not content:
            content = f"[{msg_type}]"

    try:
        await handle_inbound_message(
            db=db,
            channel="instagram_dm",
            phone_number_id=None,
            sender_id=sender_id,
            sender_name=None,
            msg_type=msg_type,
            content=content,
            channel_msg_id=message.get("mid"),
            timestamp=messaging.get("timestamp"),
        )
    except Exception:
        logger.exception("Error processing Instagram DM")


async def _handle_comment(
    db: AsyncSession, value: dict, ig_account_id: str | None,
):
    """Process an Instagram comment — auto-reply + capture lead."""
    parsed = _parse_comment_event(value)
    if not parsed:
        return

    company = await _find_company_by_ig(db, ig_account_id)
    if not company:
        return

    if not parsed["has_intent"]:
        return

    try:
        await handle_inbound_message(
            db=db,
            channel="instagram_comment",
            phone_number_id=None,
            sender_id=parsed["from_id"],
            sender_name=parsed["username"],
            msg_type="text",
            content=f"[Comentario en IG] {parsed['text']}",
            channel_msg_id=parsed["comment_id"],
        )
        logger.info(
            "Captured lead from IG comment: %s (%s)",
            parsed["username"],
            parsed["text"][:50],
        )
    except Exception:
        logger.exception("Error processing IG comment as lead")


INTENT_KEYWORDS = [
    "precio", "cuanto", "info", "disponible", "quiero",
    "interesa", "venden", "comprar", "envio",
]


def _parse_comment_event(value: dict) -> dict | None:
    """Parse Instagram comment payload into normalized dict."""
    text = value.get("text", "")
    from_user = value.get("from", {})
    from_id = from_user.get("id", "")

    if not from_id or not text:
        return None

    return {
        "comment_id": value.get("id"),
        "text": text,
        "from_id": from_id,
        "username": from_user.get("username"),
        "has_intent": any(kw in text.lower() for kw in INTENT_KEYWORDS),
    }


async def _handle_content(db: AsyncSession, value: dict, ig_account_id: str | None):
    """Auto-capture Instagram post/story content into knowledge base."""
    item_type = value.get("item")  # "post", "story", "reel"
    caption = value.get("caption", "")
    media_url = value.get("media_url", "")
    permalink = value.get("permalink", "")

    if not caption:
        return

    company = await _find_company_by_ig(db, ig_account_id)
    if not company:
        return

    # Check if already captured
    existing = await db.execute(
        select(KnowledgeItem).where(
            KnowledgeItem.company_id == company.id,
            KnowledgeItem.source == "instagram",
            KnowledgeItem.source_url == permalink,
        )
    )
    if existing.scalar_one_or_none():
        return  # Already captured

    # Create knowledge item
    kb_item = KnowledgeItem(
        company_id=company.id,
        source="instagram",
        source_url=permalink,
        source_id=value.get("id"),
        title=f"IG {item_type or 'post'}: {caption[:80]}",
        content=caption,
        media_urls=[media_url] if media_url else [],
        is_active=True,
        auto_generated=True,
    )
    db.add(kb_item)
    await db.flush()

    logger.info("Captured IG content for company %s: %s", company.slug, caption[:50])


async def _find_company_by_ig(db: AsyncSession, ig_account_id: str | None) -> Company | None:
    """Find company by Instagram account ID."""
    if not ig_account_id:
        return None
    result = await db.execute(
        select(Company).where(Company.ig_account_id == ig_account_id)
    )
    return result.scalar_one_or_none()
