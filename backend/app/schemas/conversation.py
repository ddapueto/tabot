import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class MessageResponse(BaseModel):
    id: uuid.UUID
    conversation_id: uuid.UUID
    direction: str
    sender_type: str
    msg_type: str
    content: str | None
    media_url: str | None
    channel_status: str | None
    ai_model: str | None
    ai_tokens_in: int | None
    ai_tokens_out: int | None
    ai_cost_usd: Decimal | None
    ai_tools_used: list | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationResponse(BaseModel):
    id: uuid.UUID
    lead_id: uuid.UUID
    company_id: uuid.UUID
    channel: str
    status: str
    ai_enabled: bool
    summary: str | None
    topic: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ConversationWithMessages(ConversationResponse):
    messages: list[MessageResponse] = []
