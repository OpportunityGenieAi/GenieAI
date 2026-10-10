import hashlib
import logging
import time

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.deps import get_current_user
from app.models import AcademicProfile, AppSetting, GpaProfile, Scholarship, User
from app.schemas import AdvisorResponse
from app.services.match_engine import compute_match_score

logger = logging.getLogger(__name__)

ADVISOR_SYSTEM_PROMPT = """You are a friendly, honest scholarship advisor.

NEVER guarantee a scholarship, admission, or visa outcome, or state a
success percentage. Say "appears to meet the published requirements"
instead of promising anything.

ALWAYS distinguish eligibility (can they apply), admission (will the
university accept them), and scholarship selection (will the funder pick
them) when relevant — these are separate decisions.

Treat scholarship requirements (CGPA cutoffs, IELTS, work experience,
publications) as varying by program, not universal. Never tell a student
flatly they can't get a scholarship because of one weak metric.

Research importance scales with degree level: helpful-but-optional for
undergrad, central for PhD, dominant for postdoc. Never claim
publications are mandatory for a PhD applicant.

Never suggest fabricating volunteering, publications, or achievements.

Be encouraging without being dishonest: reframe weaknesses as "areas to
strengthen," not verdicts on the student's chances."""

GENERIC_ERROR = "Couldn't reach the AI advisor just now — try again in a moment."
BUSY_ERROR = "The AI advisor is busy right now — please try again in a few minutes."

# Saves free-tier quota: the same student asking again with the same profile within
# 10 minutes gets the previous answer instead of a new model call.
CACHE_TTL_SECONDS = 600
_CACHE: dict[str, tuple[float, str, str]] = {}  # user_id -> (timestamp, prompt_hash, text)

router = APIRouter(prefix="/advisor", tags=["advisor"])


def _resolve_anthropic_key(db: Session) -> str:
    override = db.query(AppSetting).filter(AppSetting.key == "anthropic_api_key_override").first()
    if override and override.value:
        return override.value
    return settings.ANTHROPIC_API_KEY


def _call_gemini(api_key: str, prompt: str) -> str:
    """Google Gemini (free tier available through Google AI Studio)."""
    model = settings.GEMINI_MODEL
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    generation_config: dict = {"maxOutputTokens": 2048, "temperature": 0.7}
    if "2.5" in model:
        # 2.5 models spend output tokens on hidden "thinking"; turn it off so the answer is not cut short.
        generation_config["thinkingConfig"] = {"thinkingBudget": 0}
    payload = {
        "systemInstruction": {"parts": [{"text": ADVISOR_SYSTEM_PROMPT}]},
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": generation_config,
    }
    with httpx.Client(timeout=30.0) as client:
        response = client.post(
            url,
            headers={"x-goog-api-key": api_key, "content-type": "application/json"},
            json=payload,
        )
    if response.status_code == 429:
        logger.warning("Gemini rate limit reached: %s", response.text[:300])
        raise HTTPException(status_code=429, detail=BUSY_ERROR)
    if response.status_code >= 400:
        logger.error("Gemini error %s (model %s): %s", response.status_code, model, response.text[:500])
        raise HTTPException(status_code=502, detail=GENERIC_ERROR)

    data = response.json()
    candidates = data.get("candidates") or []
    parts = (candidates[0].get("content") or {}).get("parts", []) if candidates else []
    text = "\n".join(p.get("text", "") for p in parts).strip()
    if not text:
        logger.error("Gemini returned no text (model %s): %s", model, str(data)[:500])
        raise HTTPException(status_code=502, detail=GENERIC_ERROR)
    return text


def _call_anthropic(api_key: str, prompt: str) -> str:
    """Anthropic Claude (paid API, used only when no Gemini key is configured)."""
    with httpx.Client(timeout=30.0) as client:
        response = client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": settings.ANTHROPIC_MODEL,
                "max_tokens": 500,
                "system": ADVISOR_SYSTEM_PROMPT,
                "messages": [{"role": "user", "content": prompt}],
            },
        )
    if response.status_code == 429:
        logger.warning("Anthropic rate limit reached: %s", response.text[:300])
        raise HTTPException(status_code=429, detail=BUSY_ERROR)
    if response.status_code >= 400:
        # The body says why (invalid key, credit balance too low, unknown model...).
        logger.error("Anthropic error %s: %s", response.status_code, response.text[:500])
        raise HTTPException(status_code=502, detail=GENERIC_ERROR)
    data = response.json()
    text = "\n".join(block.get("text", "") for block in data.get("content", [])).strip()
    if not text:
        logger.error("Anthropic returned no text: %s", str(data)[:500])
        raise HTTPException(status_code=502, detail=GENERIC_ERROR)
    return text


@router.post("/recommend", response_model=AdvisorResponse)
def get_recommendation(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    gemini_key = settings.GEMINI_API_KEY
    anthropic_key = "" if gemini_key else _resolve_anthropic_key(db)
    if not gemini_key and not anthropic_key:
        raise HTTPException(
            status_code=503,
            detail="AI advisor isn't configured yet — set GEMINI_API_KEY (or ANTHROPIC_API_KEY) on the server.",
        )

    gpa = db.query(GpaProfile).filter(GpaProfile.user_id == current_user.id).first()
    academic = db.query(AcademicProfile).filter(AcademicProfile.user_id == current_user.id).first()
    if not gpa or not academic:
        raise HTTPException(status_code=400, detail="Complete your GPA and academic profile first.")

    scholarships = db.query(Scholarship).all()
    ranked = sorted(
        ({"s": s, "m": compute_match_score(s, gpa, academic)} for s in scholarships),
        key=lambda x: x["m"]["score"],
        reverse=True,
    )
    top_fits = "; ".join(
        f"{r['s'].name} ({r['m']['score']}% fit, needs {r['s'].level}, {r['s'].field})"
        for r in ranked[:4]
    )
    near_misses = "; ".join(
        f"{r['s'].name} ({r['m']['score']}%)"
        for r in ranked
        if 35 <= r["m"]["score"] < 70
    )

    prompt = f"""A student has this profile:
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

    prompt_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
    cached = _CACHE.get(str(current_user.id))
    if cached and cached[1] == prompt_hash and time.time() - cached[0] < CACHE_TTL_SECONDS:
        return AdvisorResponse(text=cached[2])

    try:
        text = _call_gemini(gemini_key, prompt) if gemini_key else _call_anthropic(anthropic_key, prompt)
    except HTTPException:
        raise
    except Exception:
        logger.exception("AI advisor call failed")
        raise HTTPException(status_code=502, detail=GENERIC_ERROR)

    _CACHE[str(current_user.id)] = (time.time(), prompt_hash, text)
    return AdvisorResponse(text=text)
