import hashlib
import logging
import re
import time
import uuid
from datetime import datetime, timezone
from typing import Literal, Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.deps import get_current_user
from app.models import AcademicProfile, AppSetting, GpaProfile, Scholarship, User
from app.models_chat import AdvisorConversation, AdvisorMessage
from app.schemas import AdvisorResponse
from app.services.advisor_knowledge import ADVISOR_CHAT_SYSTEM_PROMPT
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

GENERIC_ERROR = "Couldn't reach the advisor just now — try again in a moment."
BUSY_ERROR = "The advisor is busy right now — please try again in a few minutes."

# --- limits for the chat endpoint -------------------------------------------------------
MAX_MESSAGE_CHARS = 15000      # one message (a pasted statement of purpose fits easily)
MAX_HISTORY_MESSAGES = 12      # how much of the conversation is sent to the model
MAX_TOTAL_CHARS = 40000        # cap on the whole conversation sent to the model
CHAT_MAX_REQUESTS = 20         # per user ...
CHAT_WINDOW_SECONDS = 600      # ... per 10 minutes (protects the Gemini quota)

# --- saved chats ------------------------------------------------------------------------
MAX_CONVERSATIONS = 50              # per student; the oldest is removed when a new one would exceed this
MAX_MESSAGES_PER_CONVERSATION = 200

# Saves quota for /recommend: the same student asking again with the same profile
# within 10 minutes gets the previous answer instead of a new model call.
CACHE_TTL_SECONDS = 600
_CACHE: dict[str, tuple[float, str, str]] = {}  # user_id -> (timestamp, prompt_hash, text)
_CHAT_HITS: dict[str, list[float]] = {}          # user_id -> request timestamps

router = APIRouter(prefix="/advisor", tags=["advisor"])


# ======================================================================================
# model calls (Gemini preferred, Anthropic as fallback)
# ======================================================================================
def _resolve_anthropic_key(db: Session) -> str:
    override = db.query(AppSetting).filter(AppSetting.key == "anthropic_api_key_override").first()
    if override and override.value:
        return override.value
    return settings.ANTHROPIC_API_KEY


def _gemini_payload(model: str, system_prompt: str, turns: list[dict], max_tokens: int) -> dict:
    generation_config: dict = {"maxOutputTokens": max_tokens, "temperature": 0.7}
    if "2.5" in model:
        # 2.5 models spend output tokens on hidden "thinking"; turn it off so the answer is not cut short.
        generation_config["thinkingConfig"] = {"thinkingBudget": 0}
    return {
        "systemInstruction": {"parts": [{"text": system_prompt}]},
        "contents": [
            {"role": "model" if t["role"] == "assistant" else "user", "parts": [{"text": t["content"]}]}
            for t in turns
        ],
        "generationConfig": generation_config,
    }


def _gemini_text(data: dict, model: str) -> str:
    candidates = data.get("candidates") or []
    parts = (candidates[0].get("content") or {}).get("parts", []) if candidates else []
    text = "\n".join(p.get("text", "") for p in parts).strip()
    if candidates and candidates[0].get("finishReason") == "MAX_TOKENS":
        logger.warning("Gemini reply hit the output token limit (model %s)", model)
    if not text:
        logger.error("Gemini returned no text (model %s): %s", model, str(data)[:500])
    return text


def _call_gemini(api_key: str, system_prompt: str, turns: list[dict], max_tokens: int) -> str:
    """Google Gemini (free tier available through Google AI Studio).

    If a model is overloaded (503/500), over quota (429), missing (404) or returns nothing, the call is
    retried once where that makes sense and then moves on to GEMINI_FALLBACK_MODEL. Only real problems
    such as an invalid key (400/401/403) fail straight away.
    """
    models = [settings.GEMINI_MODEL]
    fallback = (settings.GEMINI_FALLBACK_MODEL or "").strip()
    if fallback and fallback not in models:
        models.append(fallback)

    saw_busy = False
    with httpx.Client(timeout=45.0) as client:
        for model in models:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
            payload = _gemini_payload(model, system_prompt, turns, max_tokens)
            for attempt in (1, 2):
                try:
                    response = client.post(
                        url,
                        headers={"x-goog-api-key": api_key, "content-type": "application/json"},
                        json=payload,
                    )
                except httpx.HTTPError as exc:
                    saw_busy = True
                    logger.warning("Gemini request failed (model %s, attempt %s): %s", model, attempt, exc)
                    if attempt == 1:
                        time.sleep(1.5)
                        continue
                    break

                status = response.status_code
                if status == 200:
                    text = _gemini_text(response.json(), model)
                    if text:
                        return text
                    break  # empty answer: try the next model
                if status in (429, 500, 503):
                    saw_busy = True
                    logger.warning("Gemini busy %s (model %s, attempt %s): %s", status, model, attempt, response.text[:300])
                    if status != 429 and attempt == 1:
                        time.sleep(1.5)
                        continue
                    break
                if status == 404:
                    logger.error("Gemini model not found/retired (model %s): %s", model, response.text[:300])
                    break
                logger.error("Gemini error %s (model %s): %s", status, model, response.text[:500])
                raise HTTPException(status_code=502, detail=GENERIC_ERROR)

    if saw_busy:
        raise HTTPException(status_code=503, detail=BUSY_ERROR)
    raise HTTPException(status_code=502, detail=GENERIC_ERROR)


def _call_anthropic(api_key: str, system_prompt: str, turns: list[dict], max_tokens: int) -> str:
    """Anthropic Claude (paid API, used only when no Gemini key is configured)."""
    with httpx.Client(timeout=60.0) as client:
        response = client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": settings.ANTHROPIC_MODEL,
                "max_tokens": max_tokens,
                "system": system_prompt,
                "messages": [{"role": t["role"], "content": t["content"]} for t in turns],
            },
        )
    if response.status_code in (429, 529):
        logger.warning("Anthropic busy %s: %s", response.status_code, response.text[:300])
        raise HTTPException(status_code=503, detail=BUSY_ERROR)
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


def _generate(db: Session, system_prompt: str, turns: list[dict], max_tokens: int) -> str:
    gemini_key = settings.GEMINI_API_KEY
    anthropic_key = "" if gemini_key else _resolve_anthropic_key(db)
    if not gemini_key and not anthropic_key:
        raise HTTPException(
            status_code=503,
            detail="The advisor isn't configured yet — set GEMINI_API_KEY (or ANTHROPIC_API_KEY) on the server.",
        )
    try:
        if gemini_key:
            return _call_gemini(gemini_key, system_prompt, turns, max_tokens)
        return _call_anthropic(anthropic_key, system_prompt, turns, max_tokens)
    except HTTPException:
        raise
    except Exception:
        logger.exception("Advisor call failed")
        raise HTTPException(status_code=502, detail=GENERIC_ERROR)


# ======================================================================================
# POST /advisor/recommend  (unchanged behaviour)
# ======================================================================================
@router.post("/recommend", response_model=AdvisorResponse)
def get_recommendation(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
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

    text = _generate(db, ADVISOR_SYSTEM_PROMPT, [{"role": "user", "content": prompt}], 2048)
    _CACHE[str(current_user.id)] = (time.time(), prompt_hash, text)
    return AdvisorResponse(text=text)


# ======================================================================================
# POST /advisor/chat  (conversation, document feedback, scholarship database, saved chats)
# ======================================================================================
class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    # Current app: send only the new `message` (and `conversation_id` to continue a saved chat);
    # the server keeps and reloads the history.
    message: Optional[str] = None
    conversation_id: Optional[str] = None
    # Older app versions send the whole conversation in `messages`; nothing is saved for those.
    messages: Optional[list[ChatTurn]] = None


class ChatResponse(BaseModel):
    text: str
    conversation_id: Optional[str] = None
    title: Optional[str] = None


class ConversationSummary(BaseModel):
    id: str
    title: str
    preview: Optional[str] = None
    updated_at: datetime


class StoredMessage(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime


class ConversationDetail(BaseModel):
    id: str
    title: str
    messages: list[StoredMessage]


def _clean_turns(messages: list[ChatTurn]) -> list[dict]:
    """Trim and tidy the conversation so the model always gets a valid, bounded history."""
    turns: list[dict] = []
    for m in messages:
        content = (m.content or "").strip()
        if not content:
            continue
        if len(content) > MAX_MESSAGE_CHARS:
            raise HTTPException(
                status_code=400,
                detail=f"That message is too long (the limit is {MAX_MESSAGE_CHARS:,} characters). "
                       "Please send it in two parts.",
            )
        if turns and turns[-1]["role"] == m.role:
            turns[-1]["content"] += "\n\n" + content  # merge consecutive messages from the same side
        else:
            turns.append({"role": m.role, "content": content})

    turns = turns[-MAX_HISTORY_MESSAGES:]
    while turns and turns[0]["role"] != "user":
        turns.pop(0)
    while len(turns) > 1 and sum(len(t["content"]) for t in turns) > MAX_TOTAL_CHARS:
        turns.pop(0)
        while turns and turns[0]["role"] != "user":
            turns.pop(0)

    if not turns or turns[-1]["role"] != "user":
        raise HTTPException(status_code=400, detail="Please type a question or paste your text.")
    return turns


def _check_rate_limit(user_id: str) -> None:
    now = time.time()
    hits = [t for t in _CHAT_HITS.get(user_id, []) if now - t < CHAT_WINDOW_SECONDS]
    if len(hits) >= CHAT_MAX_REQUESTS:
        _CHAT_HITS[user_id] = hits
        raise HTTPException(
            status_code=429,
            detail="You're sending messages quickly — please wait a minute and try again.",
        )
    hits.append(now)
    _CHAT_HITS[user_id] = hits


_STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "can", "are", "you", "your", "what", "which", "how",
    "about", "any", "have", "has", "from", "get", "give", "tell", "please", "would", "could", "should",
    "there", "their", "them", "does", "not", "but", "its", "our", "who", "why", "when", "where", "need",
    "want", "like", "some", "more", "also", "than", "then", "into", "out", "all", "one", "two", "will",
    "was", "were", "been", "being", "had", "did", "just", "me", "my", "myself", "help", "scholarship",
    "scholarships", "apply", "application", "applications",
}


def _tokens(text: str) -> list[str]:
    words = re.findall(r"[a-z0-9]+", (text or "").lower().replace("-", " "))
    seen: list[str] = []
    for w in words:
        if len(w) >= 3 and w not in _STOPWORDS and w not in seen:
            seen.append(w)
        if len(seen) >= 25:
            break
    return seen


def _tags_text(s: Scholarship) -> str:
    tags = getattr(s, "tags", None) or []
    if isinstance(tags, (list, tuple)):
        return ", ".join(str(t) for t in tags)
    return str(tags)


def _keyword_score(s: Scholarship, tokens: list[str]) -> int:
    head = " ".join(str(getattr(s, a, "") or "") for a in ("name", "provider", "country", "field", "level"))
    head = head.lower().replace("-", " ")
    rest = " ".join(str(getattr(s, a, "") or "") for a in ("funding", "blurb")) + " " + _tags_text(s)
    rest = rest.lower().replace("-", " ")
    return sum(2 for t in tokens if t in head) + sum(1 for t in tokens if t in rest)


def _scholarship_line(s: Scholarship, fit: Optional[int] = None) -> str:
    blurb = (getattr(s, "blurb", "") or "").strip().replace("\n", " ")
    if len(blurb) > 180:
        blurb = blurb[:177] + "..."
    parts = [
        f"{s.name} ({getattr(s, 'provider', '') or 'provider not stated'})",
        f"country: {getattr(s, 'country', '') or 'not stated'}",
        f"level: {getattr(s, 'level', '') or 'not stated'}",
        f"field: {getattr(s, 'field', '') or 'not stated'}",
        f"funding: {getattr(s, 'funding', '') or 'not stated'}",
        f"deadline window: {getattr(s, 'deadline_window', '') or 'not stated'}",
    ]
    tags = _tags_text(s)
    if tags:
        parts.append(f"tags: {tags}")
    if fit is not None:
        parts.append(f"fit with this student's profile: {fit}%")
    link = getattr(s, "official_link", "") or ""
    if link:
        parts.append(f"official link: {link}")
    if blurb:
        parts.append(f"summary: {blurb}")
    return "- " + " | ".join(parts)


def _build_chat_system_prompt(
    db: Session,
    gpa: Optional[GpaProfile],
    academic: Optional[AcademicProfile],
    turns: list[dict],
) -> str:
    today = datetime.now(timezone.utc).strftime("%d %B %Y")
    scholarships = db.query(Scholarship).all()

    # --- student profile (no name or email is ever sent) ---
    if gpa and academic:
        profile_block = (
            "STUDENT PROFILE (from the app):\n"
            f"- Unified GPA: {gpa.gpa:.2f}/4.0 ({gpa.percent:.0f}% US-equivalent, ECTS {gpa.ects})\n"
            f"- Seeking: {academic.level} in {academic.field or 'an unspecified field'}\n"
            f"- Nationality: {academic.nationality or 'not specified'}\n"
            f"- IELTS: {academic.ielts if academic.ielts else 'not taken'}\n"
            f"- Work experience: {academic.work_years or 0} years\n"
            f"- Publications: {academic.publications or 0}\n"
            f"- Leadership: {academic.leadership or 'None'}; Volunteering: {academic.volunteering or 'None'}"
        )
    else:
        profile_block = (
            "STUDENT PROFILE: the student has not saved GPA and academic details in the app yet. "
            "Do not assume anything about their grades; ask if it matters, and mention they can complete "
            "their profile in the app for better matches."
        )

    # --- scholarships: best profile matches + entries relevant to the latest question ---
    top_lines: list[str] = []
    seen_ids: set = set()
    if gpa and academic:
        ranked = sorted(
            ({"s": s, "m": compute_match_score(s, gpa, academic)} for s in scholarships),
            key=lambda x: x["m"]["score"],
            reverse=True,
        )
        for r in ranked[:5]:
            seen_ids.add(r["s"].id)
            top_lines.append(_scholarship_line(r["s"], r["m"]["score"]))

    user_texts = [t["content"] for t in turns if t["role"] == "user"]
    query_text = user_texts[-1][:600]
    if len(user_texts) > 1:
        query_text += " " + user_texts[-2][:300]
    tokens = _tokens(query_text)
    scored = sorted(
        ((_keyword_score(s, tokens), s) for s in scholarships),
        key=lambda x: x[0],
        reverse=True,
    )
    relevant_lines = []
    for score, s in scored:
        if score < 2 or len(relevant_lines) >= 8:
            break
        if s.id in seen_ids:
            continue
        seen_ids.add(s.id)
        relevant_lines.append(_scholarship_line(s))

    db_parts = [
        f"SCHOLARSHIP DATABASE EXTRACT (OpportunityGenie holds {len(scholarships)} scholarships; "
        "only the entries below are shown to you for this question):"
    ]
    if top_lines:
        db_parts.append("Best matches for this student's profile:\n" + "\n".join(top_lines))
    if relevant_lines:
        db_parts.append("Entries relevant to the student's latest message:\n" + "\n".join(relevant_lines))
    if not top_lines and not relevant_lines:
        db_parts.append("No entry in the database clearly matches the latest message.")

    return "\n\n".join([ADVISOR_CHAT_SYSTEM_PROMPT, f"TODAY'S DATE: {today}", profile_block, "\n\n".join(db_parts)])


# ---------- saved chats helpers ----------
def _valid_uuid(value: str) -> bool:
    try:
        uuid.UUID(str(value))
        return True
    except ValueError:
        return False


def _get_owned_conversation(db: Session, conversation_id: str, user_id: str) -> AdvisorConversation:
    if not _valid_uuid(conversation_id):
        raise HTTPException(status_code=404, detail="Chat not found.")
    convo = (
        db.query(AdvisorConversation)
        .filter(AdvisorConversation.id == conversation_id, AdvisorConversation.user_id == user_id)
        .first()
    )
    if not convo:
        raise HTTPException(status_code=404, detail="Chat not found.")
    return convo


def _make_title(text: str) -> str:
    first = ""
    for line in (text or "").splitlines():
        if line.strip():
            first = line.strip()
            break
    first = re.sub(r"\s+", " ", first)
    if not first:
        return "New chat"
    return first[:57] + "..." if len(first) > 60 else first


def _snippet(text: str, limit: int = 100) -> str:
    flat = re.sub(r"\s+", " ", text or "").strip()
    return flat[: limit - 3] + "..." if len(flat) > limit else flat


def _delete_conversation_rows(db: Session, conversation_ids: list[str]) -> None:
    if not conversation_ids:
        return
    db.query(AdvisorMessage).filter(AdvisorMessage.conversation_id.in_(conversation_ids)).delete(
        synchronize_session=False
    )
    db.query(AdvisorConversation).filter(AdvisorConversation.id.in_(conversation_ids)).delete(
        synchronize_session=False
    )


def _trim_conversations(db: Session, user_id: str) -> None:
    """Keep each student's saved chats under MAX_CONVERSATIONS by removing the oldest ones."""
    rows = (
        db.query(AdvisorConversation.id)
        .filter(AdvisorConversation.user_id == user_id)
        .order_by(AdvisorConversation.updated_at.asc())
        .all()
    )
    excess = len(rows) - (MAX_CONVERSATIONS - 1)
    if excess > 0:
        _delete_conversation_rows(db, [r[0] for r in rows[:excess]])


@router.post("/chat", response_model=ChatResponse)
def chat(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user_id = str(current_user.id)
    convo: Optional[AdvisorConversation] = None
    new_text: Optional[str] = None

    if payload.message is not None:
        new_text = payload.message.strip()
        if not new_text:
            raise HTTPException(status_code=400, detail="Please type a question or paste your text.")
        if len(new_text) > MAX_MESSAGE_CHARS:
            raise HTTPException(
                status_code=400,
                detail=f"That message is too long (the limit is {MAX_MESSAGE_CHARS:,} characters). "
                       "Please send it in two parts.",
            )
        history: list[ChatTurn] = []
        if payload.conversation_id:
            convo = _get_owned_conversation(db, payload.conversation_id, user_id)
            count = db.query(AdvisorMessage).filter(AdvisorMessage.conversation_id == str(convo.id)).count()
            if count >= MAX_MESSAGES_PER_CONVERSATION:
                raise HTTPException(
                    status_code=400,
                    detail="This chat is very long — please start a new chat to keep going.",
                )
            rows = (
                db.query(AdvisorMessage)
                .filter(AdvisorMessage.conversation_id == str(convo.id))
                .order_by(AdvisorMessage.id.desc())
                .limit(MAX_HISTORY_MESSAGES)
                .all()
            )
            rows.reverse()
            history = [ChatTurn(role=r.role, content=r.content) for r in rows]
        turns = _clean_turns(history + [ChatTurn(role="user", content=new_text)])
    elif payload.messages:
        turns = _clean_turns(payload.messages)  # older app versions: not saved
    else:
        raise HTTPException(status_code=400, detail="Please type a question or paste your text.")

    _check_rate_limit(user_id)

    gpa = db.query(GpaProfile).filter(GpaProfile.user_id == current_user.id).first()
    academic = db.query(AcademicProfile).filter(AcademicProfile.user_id == current_user.id).first()

    system_prompt = _build_chat_system_prompt(db, gpa, academic, turns)
    text = _generate(db, system_prompt, turns, 4096)

    if new_text is None:
        return ChatResponse(text=text)

    # Save the exchange (user message + reply) only after the model answered, so a failed
    # attempt never leaves a half-finished conversation behind.
    try:
        if convo is None:
            _trim_conversations(db, user_id)
            convo = AdvisorConversation(user_id=user_id, title=_make_title(new_text))
            db.add(convo)
            db.flush()
        db.add(AdvisorMessage(conversation_id=str(convo.id), role="user", content=new_text))
        db.flush()
        db.add(AdvisorMessage(conversation_id=str(convo.id), role="assistant", content=text))
        convo.preview = _snippet(text)
        convo.updated_at = datetime.now(timezone.utc)
        db.commit()
        return ChatResponse(text=text, conversation_id=str(convo.id), title=convo.title)
    except Exception:
        db.rollback()
        logger.exception("Could not save advisor conversation")
        return ChatResponse(text=text)  # the student still gets the answer, just not saved


@router.get("/conversations", response_model=list[ConversationSummary])
def list_conversations(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rows = (
        db.query(AdvisorConversation)
        .filter(AdvisorConversation.user_id == str(current_user.id))
        .order_by(AdvisorConversation.updated_at.desc())
        .limit(MAX_CONVERSATIONS)
        .all()
    )
    return [
        ConversationSummary(id=str(r.id), title=r.title, preview=r.preview, updated_at=r.updated_at)
        for r in rows
    ]


@router.get("/conversations/{conversation_id}", response_model=ConversationDetail)
def get_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    convo = _get_owned_conversation(db, conversation_id, str(current_user.id))
    rows = (
        db.query(AdvisorMessage)
        .filter(AdvisorMessage.conversation_id == str(convo.id))
        .order_by(AdvisorMessage.id.asc())
        .all()
    )
    return ConversationDetail(
        id=str(convo.id),
        title=convo.title,
        messages=[
            StoredMessage(id=r.id, role=r.role, content=r.content, created_at=r.created_at) for r in rows
        ],
    )


@router.delete("/conversations/{conversation_id}", status_code=204)
def delete_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    convo = _get_owned_conversation(db, conversation_id, str(current_user.id))
    _delete_conversation_rows(db, [str(convo.id)])
    db.commit()
    return None
