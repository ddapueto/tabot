import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base


class KnowledgeItem(Base):
    __tablename__ = "knowledge_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Source
    source: Mapped[str] = mapped_column(String(20), nullable=False)
    # Sources: catalog, document, instagram, website, faq, conversation, manual, promo
    source_url: Mapped[str | None] = mapped_column(Text)
    source_id: Mapped[str | None] = mapped_column(String(100))

    # Content
    title: Mapped[str | None] = mapped_column(String(500))
    content: Mapped[str] = mapped_column(Text, nullable=False)
    media_urls: Mapped[list | None] = mapped_column(JSONB, default=list)

    # Lifecycle
    item_type: Mapped[str] = mapped_column(String(20), default="permanent")
    # Types: permanent (FAQ, policies), temporal (promos, offers), seasonal (verano, navidad)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    priority: Mapped[int] = mapped_column(Integer, default=5)  # 1=max priority, 10=min
    # Channel targeting
    channels: Mapped[list | None] = mapped_column(JSONB, default=lambda: ["whatsapp", "instagram", "web"])
    # Which channels can use this item: whatsapp, instagram, web, all

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    auto_generated: Mapped[bool] = mapped_column(Boolean, default=False)
    needs_review: Mapped[bool] = mapped_column(Boolean, default=False)
    review_reason: Mapped[str | None] = mapped_column(String(200))

    # Usage tracking
    times_used: Mapped[int] = mapped_column(Integer, default=0)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Linked product (for catalog-sourced items)
    product_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))

    # Metadata
    metadata_extra: Mapped[dict | None] = mapped_column(JSONB, default=dict)

    # Timestamps
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
