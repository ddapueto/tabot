import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    business_type: Mapped[str | None] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text)

    # WhatsApp config
    whatsapp_phone: Mapped[str | None] = mapped_column(String(20))
    waba_id: Mapped[str | None] = mapped_column(String(50))
    phone_number_id: Mapped[str | None] = mapped_column(String(50))
    whatsapp_token: Mapped[str | None] = mapped_column(Text)

    # Instagram config
    ig_account_id: Mapped[str | None] = mapped_column(String(50))
    ig_page_id: Mapped[str | None] = mapped_column(String(50))
    ig_token: Mapped[str | None] = mapped_column(Text)

    # AI config
    ai_personality: Mapped[str | None] = mapped_column(Text)
    ai_language: Mapped[str] = mapped_column(String(50), default="es-UY")
    ai_sales_goal: Mapped[str | None] = mapped_column(Text)
    ai_custom_rules: Mapped[str | None] = mapped_column(Text)
    ai_model: Mapped[str] = mapped_column(String(50), default="claude-sonnet-4-20250514")

    # Business config
    timezone: Mapped[str] = mapped_column(String(50), default="America/Montevideo")
    business_hours: Mapped[dict | None] = mapped_column(JSONB)
    currency: Mapped[str] = mapped_column(String(3), default="USD")

    # Scoring config
    scoring_rules: Mapped[dict | None] = mapped_column(JSONB)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    leads = relationship("Lead", back_populates="company", lazy="selectin")
    products = relationship("Product", back_populates="company", lazy="selectin")
    users = relationship("User", back_populates="company", lazy="selectin")
