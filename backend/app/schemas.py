from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


# ---------- auth ----------
class SignupRequest(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(min_length=6)
    security_question: str
    security_answer: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ForgotPasswordStart(BaseModel):
    email: EmailStr


class ForgotPasswordStartResponse(BaseModel):
    security_question: str


class ForgotPasswordVerify(BaseModel):
    email: EmailStr
    security_answer: str
    new_password: str = Field(min_length=6)


class UserOut(BaseModel):
    id: str
    name: str
    email: EmailStr
    is_admin: bool
    subscription_tier: str
    preferred_locale: str

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ---------- scholarships ----------
class ScholarshipIn(BaseModel):
    name: str
    provider: str
    country: str
    level: str
    field: str = "All fields"
    funding: str = "Fully-funded"
    deadline_window: str
    official_link: str
    tags: list[str] = []
    blurb: str = ""


class ScholarshipOut(ScholarshipIn):
    id: str
    match_score: Optional[int] = None
    match_tier: Optional[str] = None

    class Config:
        from_attributes = True


# ---------- gpa converter ----------
class GpaConvertRequest(BaseModel):
    system_id: str
    value: str  # raw string; some systems (ECTS letter) aren't numeric


class GpaConvertResult(BaseModel):
    gpa: float
    percent: int
    ects: str
    percentile_note: str


class GpaProfileOut(BaseModel):
    gpa: float
    percent: float
    ects: str
    system_id: str
    system_label: str
    updated_at: datetime

    class Config:
        from_attributes = True


# ---------- academic profile ----------
class AcademicProfileIn(BaseModel):
    level: str = "Master's"
    field: str = ""
    nationality: str = ""
    ielts: Optional[float] = None
    work_years: int = 0
    publications: int = 0
    leadership: str = "None"
    volunteering: str = "None"
    has_cv: bool = False
    has_sop: bool = False
    has_recommendation_letters: bool = False


class AcademicProfileOut(AcademicProfileIn):
    updated_at: datetime

    class Config:
        from_attributes = True


class ReadinessCategory(BaseModel):
    label: str
    stars: int


class ReadinessOut(BaseModel):
    overall: int
    categories: list[ReadinessCategory]


# ---------- tracker ----------
class TrackerStatusUpdate(BaseModel):
    status: str  # saved | applied | interview | accepted | rejected


class TrackerEntryOut(BaseModel):
    scholarship_id: str
    status: str
    saved_at: datetime
    scholarship: ScholarshipOut

    class Config:
        from_attributes = True


# ---------- advisor ----------
class AdvisorResponse(BaseModel):
    text: str


# ---------- billing ----------
class CheckoutSessionResponse(BaseModel):
    checkout_url: str


# ---------- app settings (admin-managed config) ----------
class AppSettingIn(BaseModel):
    value: str


class AppSettingOut(BaseModel):
    key: str
    value: Optional[str] = None

    class Config:
        from_attributes = True
