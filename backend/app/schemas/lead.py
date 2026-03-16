import uuid
from datetime import datetime

from pydantic import BaseModel


class LeadResponse(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    name: str | None
    whatsapp_phone: str | None
    instagram_username: str | None
    email: str | None
    city: str | None
    score: int
    stage: str
    priority: str
    budget_range: str | None
    timeline: str | None
    needs_summary: str | None
    source_channel: str | None
    tags: list | None
    last_message_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class LeadUpdate(BaseModel):
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    city: str | None = None
    stage: str | None = None
    priority: str | None = None
    budget_range: str | None = None
    timeline: str | None = None
    needs_summary: str | None = None
    tags: list[str] | None = None
    notes: str | None = None
    assigned_to: uuid.UUID | None = None
