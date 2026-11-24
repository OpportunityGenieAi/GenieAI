"""Paid consultation bookings and the documents students attach to them."""
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, LargeBinary, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base
from app.models import gen_uuid


class Consultation(Base):
    __tablename__ = "consultations"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(String, nullable=False)
    minutes = Column(Integer, nullable=False)
    purchase_token = Column(String, unique=True, nullable=False, index=True)
    order_id = Column(String, nullable=True)
    upload_token = Column(String, unique=True, nullable=False, index=True)
    status = Column(String, nullable=False, default="paid")  # paid -> submitted
    is_test = Column(Boolean, default=False, nullable=False)

    full_name = Column(String, nullable=True)
    email = Column(String, nullable=True)
    country = Column(String, nullable=True)
    education_level = Column(String, nullable=True)
    study_interest = Column(String, nullable=True)
    applied_scholarships = Column(Text, nullable=True)
    academic_summary = Column(Text, nullable=True)
    availability = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)

    email_sent = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    submitted_at = Column(DateTime, nullable=True)


class ConsultationFile(Base):
    __tablename__ = "consultation_files"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    consultation_id = Column(
        UUID(as_uuid=False), ForeignKey("consultations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    filename = Column(String, nullable=False)
    content_type = Column(String, nullable=False)
    size = Column(Integer, nullable=False)
    data = Column(LargeBinary, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
