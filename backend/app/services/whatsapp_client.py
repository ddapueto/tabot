import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

BASE_URL = "https://graph.facebook.com/v21.0"


async def send_text_message(phone_number_id: str, to: str, text: str) -> dict:
    """Send a text message via WhatsApp Cloud API."""
    url = f"{BASE_URL}/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {settings.whatsapp_access_token}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "text",
        "text": {"preview_url": False, "body": text},
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        logger.info("Message sent to %s, wamid: %s", to, data.get("messages", [{}])[0].get("id"))
        return data


async def send_image_message(phone_number_id: str, to: str, image_url: str, caption: str | None = None) -> dict:
    """Send an image message via WhatsApp Cloud API."""
    url = f"{BASE_URL}/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {settings.whatsapp_access_token}",
        "Content-Type": "application/json",
    }
    image_data: dict = {"link": image_url}
    if caption:
        image_data["caption"] = caption

    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "image",
        "image": image_data,
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()


async def send_interactive_buttons(
    phone_number_id: str, to: str, body_text: str, buttons: list[dict]
) -> dict:
    """Send interactive button message (max 3 buttons)."""
    url = f"{BASE_URL}/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {settings.whatsapp_access_token}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": body_text},
            "action": {
                "buttons": [
                    {"type": "reply", "reply": {"id": b["id"], "title": b["title"]}}
                    for b in buttons[:3]
                ]
            },
        },
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
