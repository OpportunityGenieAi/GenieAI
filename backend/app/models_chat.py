"""Saved advisor chats (one conversation has many messages)."""
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, func

from app.database import Base
from app.models import gen_uuid


class AdvisorConversation(Base):
    __tablename__ = "advisor_conversations"

    id = Column(String, primary_key=True, default=gen_uuid)
    user_id = Column(String, nullable=False, index=True)
    title = Column(String, nullable=False, default="New chat")
    preview = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class AdvisorMessage(Base):
    __tablename__ = "advisor_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(
        String,
        ForeignKey("advisor_conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role = Column(String, nullable=False)  # "user" | "assistant"
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
