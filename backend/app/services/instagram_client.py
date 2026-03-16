"""Instagram Graph API client — send DMs and reply to comments."""

import logging

import httpx

logger = logging.getLogger(__name__)

BASE_URL = "https://graph.facebook.com/v21.0"


async def send_dm(ig_page_id: str, access_token: str, recipient_id: str, text: str) -> dict:
    """Send a DM via Instagram Messaging API."""
    url = f"{BASE_URL}/{ig_page_id}/messages"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": text},
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        logger.info("IG DM sent to %s", recipient_id)
        return data


async def reply_to_comment(comment_id: str, access_token: str, text: str) -> dict:
    """Reply to an Instagram comment."""
    url = f"{BASE_URL}/{comment_id}/replies"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    payload = {"message": text}

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
