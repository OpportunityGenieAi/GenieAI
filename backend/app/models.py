import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text, JSON
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


def gen_uuid():
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)

    # Passwords and email confirmation / reset now live in Supabase Auth.
    # These three columns are legacy: only accounts created before the
    # Supabase switch still have values (they can keep logging in with the
    # old password). New accounts leave them empty.
    password_hash = Column(String, nullable=True)
    security_question = Column(String, nullable=True)
    security_answer_hash = Column(String, nullable=True)

    is_admin = Column(Boolean, default=False, nullable=False)
    subscription_tier = Column(String, default="free", nullable=False)  # free | premium
    stripe_customer_id = Column(String, nullable=True)

    preferred_locale = Column(String, default="en", nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    gpa_profile = relationship("GpaProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    academic_profile = relationship("AcademicProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    tracker_entries = relationship("TrackerEntry", back_populates="user", cascade="all, delete-orphan")


class Scholarship(Base):
    __tablename__ = "scholarships"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    name = Column(String, nullable=False)
    provider = Column(String, nullable=False)
    country = Column(String, nullable=False)
    level = Column(String, nullable=False)
    field = Column(String, default="All fields")
    funding = Column(String, default="Fully-funded")
    deadline_window = Column(String, nullable=False)
    official_link = Column(String, nullable=False)
    tags = Column(JSON, default=list)
    blurb = Column(Text, default="")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class GpaProfile(Base):
    __tablename__ = "gpa_profiles"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), unique=True, nullable=False)

    gpa = Column(Float, nullable=False)
    percent = Column(Float, nullable=False)
    ects = Column(String, nullable=False)
    system_id = Column(String, nullable=False)
    system_label = Column(String, nullable=False)

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="gpa_profile")


class AcademicProfile(Base):
    __tablename__ = "academic_profiles"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), unique=True, nullable=False)

    level = Column(String, default="Master's")
    field = Column(String, default="")
    nationality = Column(String, default="")
    ielts = Column(Float, nullable=True)
    work_years = Column(Integer, default=0)
    publications = Column(Integer, default=0)
    leadership = Column(String, default="None")       # None | Some | Extensive
    volunteering = Column(String, default="None")      # None | Occasional | Regular
    has_cv = Column(Boolean, default=False)
    has_sop = Column(Boolean, default=False)
    has_recommendation_letters = Column(Boolean, default=False)

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="academic_profile")


class AppSetting(Base):
    """
    Admin-editable key/value configuration — lets the admin change things
    like AdMob ad unit IDs or third-party API keys from inside the app
    itself, without needing access to Render's dashboard.

    Ad unit IDs read from here take effect immediately (the app fetches
    them at runtime). Anything baked into a native build (like the AdMob
    App ID itself) still needs a real rebuild to change — this table
    can't override that, only runtime-readable values.
    """
    __tablename__ = "app_settings"

    key = Column(String, primary_key=True)
    value = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TrackerEntry(Base):
    __tablename__ = "tracker_entries"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    scholarship_id = Column(UUID(as_uuid=False), ForeignKey("scholarships.id"), nullable=False)

    status = Column(String, default="saved")  # saved | applied | interview | accepted | rejected
    saved_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="tracker_entries")
    scholarship = relationship("Scholarship")
