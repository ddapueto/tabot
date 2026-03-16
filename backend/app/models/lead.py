import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class Lead(Base):
    __tablename__ = "leads"
    __table_args__ = (
        UniqueConstraint("company_id", "whatsapp_id", name="uq_lead_whatsapp"),
        UniqueConstraint("company_id", "instagram_id", name="uq_lead_instagram"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Channel IDs
    whatsapp_id: Mapped[str | None] = mapped_column(String(50))
    whatsapp_phone: Mapped[str | None] = mapped_column(String(20))
    instagram_id: Mapped[str | None] = mapped_column(String(50))
    instagram_username: Mapped[str | None] = mapped_column(String(100))

    # Contact info
    name: Mapped[str | None] = mapped_column(String(200))
    email: Mapped[str | None] = mapped_column(String(200))
    phone: Mapped[str | None] = mapped_column(String(20))
    city: Mapped[str | None] = mapped_column(String(100))
    region: Mapped[str | None] = mapped_column(String(100))

    # Scoring & pipeline
    score: Mapped[int] = mapped_column(Integer, default=0)
    stage: Mapped[str] = mapped_column(String(30), default="new", index=True)
    priority: Mapped[str] = mapped_column(String(10), default="medium")

    # Interest
    budget_range: Mapped[str | None] = mapped_column(String(50))
    interested_products: Mapped[list | None] = mapped_column(JSONB, default=list)
    timeline: Mapped[str | None] = mapped_column(String(50))
    needs_summary: Mapped[str | None] = mapped_column(Text)

    # Source
    source_channel: Mapped[str | None] = mapped_column(String(20))
    source_campaign: Mapped[str | None] = mapped_column(String(100))
    source_url: Mapped[str | None] = mapped_column(Text)

    # Assignment
    assigned_to: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))

    # Metadata
    tags: Mapped[list | None] = mapped_column(JSONB, default=list)
    notes: Mapped[str | None] = mapped_column(Text)
    custom_fields: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    last_message_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_response_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    company = relationship("Company", back_populates="leads")
    conversations = relationship("Conversation", back_populates="lead", lazy="selectin")
    stage_history = relationship("LeadStageHistory", back_populates="lead", lazy="selectin")


class LeadStageHistory(Base):
    __tablename__ = "lead_stage_history"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lead_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, index=True
    )
    from_stage: Mapped[str | None] = mapped_column(String(30))
    to_stage: Mapped[str] = mapped_column(String(30), nullable=False)
    changed_by: Mapped[str | None] = mapped_column(String(50))
    reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    lead = relationship("Lead", back_populates="stage_history")
