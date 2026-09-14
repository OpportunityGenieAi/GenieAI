from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import AcademicProfile, GpaProfile, User
from app.schemas import (
    AcademicProfileIn, AcademicProfileOut, GpaConvertRequest, GpaConvertResult,
    GpaProfileOut, ReadinessOut,
)
from app.services.gpa_converter import SYSTEMS, InvalidValueError, UnknownSystemError, compute_conversion
from app.services.match_engine import compute_readiness

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("/gpa/systems")
def list_gpa_systems():
    """Returns the selectable grading systems for the converter's dropdown."""
    return [
        {"id": s.id, "label": s.label, "input_type": s.input_type, "min": s.min, "max": s.max, "options": s.options}
        for s in SYSTEMS
    ]


@router.post("/gpa/convert", response_model=GpaConvertResult)
def convert_gpa(payload: GpaConvertRequest):
    try:
        result = compute_conversion(payload.system_id, payload.value)
    except UnknownSystemError:
        raise HTTPException(status_code=400, detail="Unknown grading system.")
    except InvalidValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return GpaConvertResult(**result)


@router.post("/gpa", response_model=GpaProfileOut)
def save_gpa_profile(payload: GpaConvertRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        result = compute_conversion(payload.system_id, payload.value)
    except UnknownSystemError:
        raise HTTPException(status_code=400, detail="Unknown grading system.")
    except InvalidValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    system_label = next((s.label for s in SYSTEMS if s.id == payload.system_id), payload.system_id)
    profile = db.query(GpaProfile).filter(GpaProfile.user_id == current_user.id).first()
    if not profile:
        profile = GpaProfile(user_id=current_user.id)
        db.add(profile)

    profile.gpa = result["gpa"]
    profile.percent = result["percent"]
    profile.ects = result["ects"]
    profile.system_id = payload.system_id
    profile.system_label = system_label
    db.commit()
    db.refresh(profile)
    return GpaProfileOut.model_validate(profile)


@router.get("/gpa", response_model=GpaProfileOut | None)
def get_gpa_profile(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    profile = db.query(GpaProfile).filter(GpaProfile.user_id == current_user.id).first()
    return GpaProfileOut.model_validate(profile) if profile else None


@router.post("/academic", response_model=AcademicProfileOut)
def save_academic_profile(payload: AcademicProfileIn, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    profile = db.query(AcademicProfile).filter(AcademicProfile.user_id == current_user.id).first()
    if not profile:
        profile = AcademicProfile(user_id=current_user.id)
        db.add(profile)
    for key, value in payload.model_dump().items():
        setattr(profile, key, value)
    db.commit()
    db.refresh(profile)
    return AcademicProfileOut.model_validate(profile)


@router.get("/academic", response_model=AcademicProfileOut | None)
def get_academic_profile(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    profile = db.query(AcademicProfile).filter(AcademicProfile.user_id == current_user.id).first()
    return AcademicProfileOut.model_validate(profile) if profile else None


@router.get("/readiness", response_model=ReadinessOut | None)
def get_readiness(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    gpa = db.query(GpaProfile).filter(GpaProfile.user_id == current_user.id).first()
    academic = db.query(AcademicProfile).filter(AcademicProfile.user_id == current_user.id).first()
    result = compute_readiness(gpa, academic)
    return ReadinessOut(**result) if result else None
