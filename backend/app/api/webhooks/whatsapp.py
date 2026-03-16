import hashlib
import hmac
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.services.message_handler import handle_inbound_message

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/whatsapp")
async def verify_webhook(
    hub_mode: str = Query(alias="hub.mode", default=""),
    hub_verify_token: str = Query(alias="hub.verify_token", default=""),
    hub_challenge: str = Query(alias="hub.challenge", default=""),
):
    """Meta webhook verification endpoint."""
    if hub_mode == "subscribe" and hub_verify_token == settings.meta_verify_token:
        logger.info("Webhook verified successfully")
        return int(hub_challenge)
    raise HTTPException(status_code=403, detail="Verification failed")


def verify_signature(payload: bytes, signature: str) -> bool:
    """Verify Meta webhook HMAC-SHA256 signature."""
    if not settings.meta_app_secret:
        return True  # Skip in development
    expected = hmac.new(
        settings.meta_app_secret.encode(),
        payload,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)


@router.post("/whatsapp")
async def receive_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """Receive WhatsApp messages via Meta Cloud API webhook."""
    body = await request.body()

    # Verify HMAC signature
    signature = request.headers.get("X-Hub-Signature-256", "")
    if not verify_signature(body, signature):
        raise HTTPException(status_code=403, detail="Invalid signature")

    payload = await request.json()

    # Process each entry
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            if change.get("field") != "messages":
                continue

            value = change.get("value", {})
            phone_number_id = value.get("metadata", {}).get("phone_number_id")
            messages = value.get("messages", [])
            contacts = value.get("contacts", [])

            for msg in messages:
                contact = next(
                    (c for c in contacts if c.get("wa_id") == msg.get("from")),
                    {},
                )
                try:
                    await handle_inbound_message(
                        db=db,
                        channel="whatsapp",
                        phone_number_id=phone_number_id,
                        sender_id=msg.get("from", ""),
                        sender_name=contact.get("profile", {}).get("name"),
                        msg_type=msg.get("type", "text"),
                        content=msg.get("text", {}).get("body", ""),
                        channel_msg_id=msg.get("id"),
                        timestamp=msg.get("timestamp"),
                        raw_payload=msg,
                    )
                except Exception:
                    logger.exception("Error processing WhatsApp message")

    return {"status": "ok"}
