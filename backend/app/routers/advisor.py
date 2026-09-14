import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.deps import get_current_user
from app.models import AcademicProfile, GpaProfile, Scholarship, User
from app.schemas import AdvisorResponse
from app.services.match_engine import compute_match_score

router = APIRouter(prefix="/advisor", tags=["advisor"])


@router.post("/recommend", response_model=AdvisorResponse)
def get_recommendation(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not settings.ANTHROPIC_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="AI advisor isn't configured yet — set ANTHROPIC_API_KEY on the server."
        )

    gpa = db.query(GpaProfile).filter(GpaProfile.user_id == current_user.id).first()
    academic = db.query(AcademicProfile).filter(AcademicProfile.user_id == current_user.id).first()
    if not gpa or not academic:
        raise HTTPException(status_code=400, detail="Complete your GPA and academic profile first.")

    scholarships = db.query(Scholarship).all()
    ranked = sorted(
        ({"s": s, "m": compute_match_score(s, gpa, academic)} for s in scholarships),
        key=lambda x: x["m"]["score"], reverse=True,
    )
    top_fits = "; ".join(f"{r['s'].name} ({r['m']['score']}% fit, needs {r['s'].level}, {r['s'].field})" for r in ranked[:4])
    near_misses = "; ".join(f"{r['s'].name} ({r['m']['score']}%)" for r in ranked if 35 <= r["m"]["score"] < 70)

    prompt = f"""You are a friendly, honest scholarship advisor. A student has this profile:
- Unified GPA: {gpa.gpa:.2f}/4.0 ({gpa.percent:.0f}% US-equivalent, ECTS {gpa.ects})
- Seeking: {academic.level} in {academic.field or 'an unspecified field'}
- Nationality: {academic.nationality or 'not specified'}
- IELTS: {academic.ielts if academic.ielts else 'not taken'}
- Work experience: {academic.work_years or 0} years
- Publications: {academic.publications or 0}
- Leadership: {academic.leadership or 'None'}, Volunteering: {academic.volunteering or 'None'}

Best-fitting scholarships: {top_fits or 'none found'}.
Near-miss scholarships: {near_misses[:400] if near_misses else 'none found'}.

In under 140 words, give: (1) one honest sentence on overall competitiveness, (2) two or three
concrete actions that would most improve chances, each with the likely benefit. Plain text,
second person, encouraging but realistic."""

    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": settings.ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": settings.ANTHROPIC_MODEL,
                    "max_tokens": 500,
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
            response.raise_for_status()
            data = response.json()
            text = "\n".join(block.get("text", "") for block in data.get("content", [])).strip()
            if not text:
                raise ValueError("empty response from model")
            return AdvisorResponse(text=text)
    except Exception:
        raise HTTPException(status_code=502, detail="Couldn't reach the AI advisor just now — try again in a moment.")
