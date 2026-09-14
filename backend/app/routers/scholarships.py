from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_admin, get_current_user_optional
from app.models import AcademicProfile, GpaProfile, Scholarship, User
from app.schemas import ScholarshipIn, ScholarshipOut
from app.services.match_engine import compute_match_score

router = APIRouter(prefix="/scholarships", tags=["scholarships"])


@router.get("", response_model=list[ScholarshipOut])
def list_scholarships(
    q: Optional[str] = Query(None, description="Free-text search across name, country, field"),
    region: Optional[str] = Query(None, description="UK | USA | Europe | Africa | Asia | Other | All"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    query = db.query(Scholarship)
    scholarships = query.all()

    if q:
        needle = q.lower()
        scholarships = [
            s for s in scholarships
            if needle in s.name.lower() or needle in s.country.lower()
            or needle in (s.field or "").lower() or needle in s.provider.lower()
        ]

    if region and region != "All":
        scholarships = [s for s in scholarships if _region_of(s.country) == region]

    gpa_profile = academic_profile = None
    if current_user:
        gpa_profile = db.query(GpaProfile).filter(GpaProfile.user_id == current_user.id).first()
        academic_profile = db.query(AcademicProfile).filter(AcademicProfile.user_id == current_user.id).first()

    results = []
    for s in scholarships:
        out = ScholarshipOut.model_validate(s)
        if gpa_profile or academic_profile:
            m = compute_match_score(s, gpa_profile, academic_profile)
            out.match_score, out.match_tier = m["score"], m["tier"]
        results.append(out)
    return results


def _region_of(country: str) -> str:
    c = (country or "").lower()
    if "united kingdom" in c: return "UK"
    if "united states" in c: return "USA"
    if any(x in c for x in ["germany", "france", "italy", "spain", "netherlands", "switzerland", "turkey", "europe"]):
        return "Europe"
    if any(x in c for x in ["africa", "zambia", "zimbabwe", "malawi"]):
        return "Africa"
    if any(x in c for x in ["japan", "china", "korea", "asia"]):
        return "Asia"
    return "Other"


@router.post("", response_model=ScholarshipOut, status_code=201)
def create_scholarship(payload: ScholarshipIn, db: Session = Depends(get_db), _admin: User = Depends(get_current_admin)):
    scholarship = Scholarship(**payload.model_dump())
    db.add(scholarship)
    db.commit()
    db.refresh(scholarship)
    return ScholarshipOut.model_validate(scholarship)


@router.put("/{scholarship_id}", response_model=ScholarshipOut)
def update_scholarship(scholarship_id: str, payload: ScholarshipIn, db: Session = Depends(get_db), _admin: User = Depends(get_current_admin)):
    scholarship = db.query(Scholarship).filter(Scholarship.id == scholarship_id).first()
    if not scholarship:
        raise HTTPException(status_code=404, detail="Scholarship not found")
    for key, value in payload.model_dump().items():
        setattr(scholarship, key, value)
    db.commit()
    db.refresh(scholarship)
    return ScholarshipOut.model_validate(scholarship)


@router.delete("/{scholarship_id}", status_code=204)
def delete_scholarship(scholarship_id: str, db: Session = Depends(get_db), _admin: User = Depends(get_current_admin)):
    scholarship = db.query(Scholarship).filter(Scholarship.id == scholarship_id).first()
    if not scholarship:
        raise HTTPException(status_code=404, detail="Scholarship not found")
    db.delete(scholarship)
    db.commit()
    return None
