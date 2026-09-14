from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import Scholarship, TrackerEntry, User
from app.schemas import TrackerEntryOut, TrackerStatusUpdate

router = APIRouter(prefix="/tracker", tags=["tracker"])

VALID_STATUSES = {"saved", "applied", "interview", "accepted", "rejected"}


@router.get("", response_model=list[TrackerEntryOut])
def list_tracker(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    entries = db.query(TrackerEntry).filter(TrackerEntry.user_id == current_user.id).all()
    return [TrackerEntryOut.model_validate(e) for e in entries]


@router.post("/{scholarship_id}", response_model=TrackerEntryOut, status_code=201)
def add_tracker_entry(scholarship_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    scholarship = db.query(Scholarship).filter(Scholarship.id == scholarship_id).first()
    if not scholarship:
        raise HTTPException(status_code=404, detail="Scholarship not found")

    existing = db.query(TrackerEntry).filter(
        TrackerEntry.user_id == current_user.id, TrackerEntry.scholarship_id == scholarship_id
    ).first()
    if existing:
        return TrackerEntryOut.model_validate(existing)

    entry = TrackerEntry(user_id=current_user.id, scholarship_id=scholarship_id, status="saved")
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return TrackerEntryOut.model_validate(entry)


@router.patch("/{scholarship_id}", response_model=TrackerEntryOut)
def update_tracker_status(scholarship_id: str, payload: TrackerStatusUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if payload.status not in VALID_STATUSES:
        raise HTTPException(status_code=422, detail=f"Status must be one of {sorted(VALID_STATUSES)}")
    entry = db.query(TrackerEntry).filter(
        TrackerEntry.user_id == current_user.id, TrackerEntry.scholarship_id == scholarship_id
    ).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Not tracked yet")
    entry.status = payload.status
    db.commit()
    db.refresh(entry)
    return TrackerEntryOut.model_validate(entry)


@router.delete("/{scholarship_id}", status_code=204)
def remove_tracker_entry(scholarship_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    entry = db.query(TrackerEntry).filter(
        TrackerEntry.user_id == current_user.id, TrackerEntry.scholarship_id == scholarship_id
    ).first()
    if entry:
        db.delete(entry)
        db.commit()
    return None
