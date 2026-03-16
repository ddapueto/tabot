import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Direction
    direction: Mapped[str] = mapped_column(String(10), nullable=False)  # inbound, outbound
    sender_type: Mapped[str] = mapped_column(String(10), nullable=False)  # lead, ai, human
    sender_id: Mapped[str | None] = mapped_column(String(100))

    # Content
    msg_type: Mapped[str] = mapped_column(String(20), nullable=False)  # text, image, audio, etc.
    content: Mapped[str | None] = mapped_column(Text)
    media_url: Mapped[str | None] = mapped_column(Text)
    media_mime: Mapped[str | None] = mapped_column(String(50))

    # Channel metadata
    channel_msg_id: Mapped[str | None] = mapped_column(String(100), index=True)
    channel_status: Mapped[str | None] = mapped_column(String(20))

    # AI metadata
    ai_model: Mapped[str | None] = mapped_column(String(50))
    ai_tokens_in: Mapped[int | None] = mapped_column(Integer)
    ai_tokens_out: Mapped[int | None] = mapped_column(Integer)
    ai_cost_usd: Mapped[Decimal | None] = mapped_column(Numeric(8, 6))
    ai_tools_used: Mapped[list | None] = mapped_column(JSONB)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    channel_ts: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    conversation = relationship("Conversation", back_populates="messages")
