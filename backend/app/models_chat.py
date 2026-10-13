"""Saved advisor conversations.

Two small tables, created automatically when the backend starts (Base.metadata.create_all).
user_id is stored as plain text without a foreign key so this module cannot clash with the
type of the users table.
"""
import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class AdvisorConversation(Base):
    __tablename__ = "advisor_conversations"

    id = Column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)
    title = Column(String(120), nullable=False, default="New chat")
    preview = Column(String(200), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class AdvisorMessage(Base):
    __tablename__ = "advisor_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)  # ids increase, so id order = message order
    conversation_id = Column(
        UUID(as_uuid=False),
        ForeignKey("advisor_conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role = Column(String(16), nullable=False)  # "user" or "assistant"
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
