"""Saved advisor chats (one conversation = many messages). Tables are created automatically on startup."""
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


def _new_id() -> str:
    return str(uuid.uuid4())


class AdvisorConversation(Base):
    __tablename__ = "advisor_conversations"

    id = Column(UUID(as_uuid=False), primary_key=True, default=_new_id)
    user_id = Column(String, nullable=False, index=True)   # the owner; every query filters by this
    title = Column(String, nullable=False, default="New chat")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, index=True)


class AdvisorMessage(Base):
    __tablename__ = "advisor_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(UUID(as_uuid=False), nullable=False, index=True)
    role = Column(String, nullable=False)                   # "user" or "assistant"
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
