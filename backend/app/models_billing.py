"""Google Play subscriptions: one row per purchase token."""
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base
from app.models import gen_uuid


class PlaySubscription(Base):
    __tablename__ = "play_subscriptions"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id = Column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    purchase_token = Column(String, unique=True, nullable=False, index=True)
    product_id = Column(String, nullable=False)
    state = Column(String, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    auto_renewing = Column(Boolean, default=False, nullable=False)
    is_test = Column(Boolean, default=False, nullable=False)
    order_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
