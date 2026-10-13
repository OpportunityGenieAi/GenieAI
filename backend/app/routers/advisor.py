import hashlib
import logging
import re
import time
from datetime import datetime, timezone
from typing import Literal, Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.deps import get_current_user
from app.models import AcademicProfile, AppSetting, GpaProfile, Scholarship, User
from app.models_advisor import AdvisorConversation, AdvisorMessage
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

GENERIC_ERROR = "Couldn't reach the AI advisor just now — try again in a moment."
BUSY_ERROR = "The AI advisor is busy right now — please try again in a few minutes."

# --- limits for the chat endpoint -------------------------------------------------------
MAX_MESSAGE_CHARS = 15000      # one message (a pasted statement of purpose fits easily)
MAX_HISTORY_MESSAGES = 12      # how much of the conversation is sent to the model
MAX_TOTAL_CHARS = 40000        # cap on the whole conversation sent to the model
CHAT_MAX_REQUESTS = 20         # per user ...
CHAT_WINDOW_SECONDS = 600      # ... per 10 minutes (protects the free Gemini quota)
MAX_SAVED_CHATS = 50           # how many saved chats the History list returns

# Saves free-tier quota for /recommend: the same student asking again with the same profile
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


def _call_gemini(api_key: str, system_prompt: str, turns: list[dict], max_tokens: int) -> str:
    """Google Gemini (free tier available through Google AI Studio)."""
    model = settings.GEMINI_MODEL
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    generation_config: dict = {"maxOutputTokens": max_tokens, "temperature": 0.7}
    if "2.5" in model:
        # 2.5 models spend output tokens on hidden "thinking"; turn it off so the answer is not cut short.
        generation_config["thinkingConfig"] = {"thinkingBudget": 0}
    payload = {
        "systemInstruction": {"parts": [{"text": system_prompt}]},
        "contents": [
            {"role": "model" if t["role"] == "assistant" else "user", "parts": [{"text": t["content"]}]}
            for t in turns
        ],
        "generationConfig": generation_config,
    }
    with httpx.Client(timeout=60.0) as client:
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
    if candidates and candidates[0].get("finishReason") == "MAX_TOKENS":
        logger.warning("Gemini reply hit the output token limit (model %s)", model)
    if not text:
        logger.error("Gemini returned no text (model %s): %s", model, str(data)[:500])
        raise HTTPException(status_code=502, detail=GENERIC_ERROR)
    return text


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


def _generate(db: Session, system_prompt: str, turns: list[dict], max_tokens: int) -> str:
    gemini_key = settings.GEMINI_API_KEY
    anthropic_key = "" if gemini_key else _resolve_anthropic_key(db)
    if not gemini_key and not anthropic_key:
        raise HTTPException(
            status_code=503,
            detail="AI advisor isn't configured yet — set GEMINI_API_KEY (or ANTHROPIC_API_KEY) on the server.",
        )
    try:
        if gemini_key:
            return _call_gemini(gemini_key, system_prompt, turns, max_tokens)
        return _call_anthropic(anthropic_key, system_prompt, turns, max_tokens)
    except HTTPException:
        raise
    except Exception:
        logger.exception("AI advisor call failed")
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
# POST /advisor/chat  (open conversation, document feedback, scholarship database)
# ======================================================================================
class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    # Current app: one new message plus (optionally) the id of the saved chat to continue.
    message: Optional[str] = None
    conversation_id: Optional[str] = None
    # Older app builds: the whole conversation sent each time (nothing is saved).
    messages: Optional[list[ChatTurn]] = None


class ChatResponse(BaseModel):
    text: str
    conversation_id: Optional[str] = None
    title: Optional[str] = None


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


def _make_title(first_message: str) -> str:
    title = " ".join((first_message or "").split())
    if not title:
        return "New chat"
    return title if len(title) <= 60 else title[:57].rstrip() + "..."


def _iso(dt: Optional[datetime]) -> str:
    return (dt.isoformat() + "Z") if dt else ""


def _own_conversation(db: Session, conversation_id: str, user_id: str) -> Optional[AdvisorConversation]:
    """A student can only ever reach their own chats."""
    try:
        return (
            db.query(AdvisorConversation)
            .filter(AdvisorConversation.id == conversation_id, AdvisorConversation.user_id == user_id)
            .first()
        )
    except Exception:  # e.g. the id is not a valid UUID
        db.rollback()
        return None


@router.post("/chat", response_model=ChatResponse)
def chat(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user_id = str(current_user.id)
    gpa = db.query(GpaProfile).filter(GpaProfile.user_id == current_user.id).first()
    academic = db.query(AcademicProfile).filter(AcademicProfile.user_id == current_user.id).first()

    # ---- older app builds: stateless chat, the whole conversation is sent each time ----
    if payload.message is None:
        if not payload.messages:
            raise HTTPException(status_code=400, detail="Please type a question or paste your text.")
        turns = _clean_turns(payload.messages)
        _check_rate_limit(user_id)
        system_prompt = _build_chat_system_prompt(db, gpa, academic, turns)
        return ChatResponse(text=_generate(db, system_prompt, turns, 4096))

    # ---- current app: one message, history kept on the server ----
    content = payload.message.strip()
    if not content:
        raise HTTPException(status_code=400, detail="Please type a question or paste your text.")
    if len(content) > MAX_MESSAGE_CHARS:
        raise HTTPException(
            status_code=400,
            detail=f"That message is too long (the limit is {MAX_MESSAGE_CHARS:,} characters). "
                   "Please send it in two parts.",
        )

    conversation: Optional[AdvisorConversation] = None
    history: list[ChatTurn] = []
    if payload.conversation_id:
        conversation = _own_conversation(db, payload.conversation_id, user_id)
        if conversation is None:
            raise HTTPException(status_code=404, detail="That chat could not be found. Start a new chat.")
        rows = (
            db.query(AdvisorMessage)
            .filter(AdvisorMessage.conversation_id == conversation.id)
            .order_by(AdvisorMessage.id.desc())
            .limit(MAX_HISTORY_MESSAGES)
            .all()
        )
        history = [ChatTurn(role=r.role, content=r.content) for r in reversed(rows)]

    turns = _clean_turns(history + [ChatTurn(role="user", content=content)])
    _check_rate_limit(user_id)

    system_prompt = _build_chat_system_prompt(db, gpa, academic, turns)
    text = _generate(db, system_prompt, turns, 4096)

    # Save only after a successful reply, so a failed attempt never leaves half a conversation behind.
    if conversation is None:
        conversation = AdvisorConversation(user_id=user_id, title=_make_title(content))
        db.add(conversation)
        db.flush()
    db.add(AdvisorMessage(conversation_id=conversation.id, role="user", content=content))
    db.add(AdvisorMessage(conversation_id=conversation.id, role="assistant", content=text))
    conversation.updated_at = datetime.utcnow()
    db.commit()
    return ChatResponse(text=text, conversation_id=str(conversation.id), title=conversation.title)


# ======================================================================================
# Saved chats: History list, open a chat, delete a chat
# ======================================================================================
class ConversationSummary(BaseModel):
    id: str
    title: str
    preview: Optional[str] = None
    updated_at: str


class StoredMessageOut(BaseModel):
    id: int
    role: str
    content: str
    created_at: str


class ConversationDetail(BaseModel):
    id: str
    title: str
    messages: list[StoredMessageOut]


@router.get("/conversations", response_model=list[ConversationSummary])
def list_conversations(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    convos = (
        db.query(AdvisorConversation)
        .filter(AdvisorConversation.user_id == str(current_user.id))
        .order_by(AdvisorConversation.updated_at.desc())
        .limit(MAX_SAVED_CHATS)
        .all()
    )
    out: list[ConversationSummary] = []
    for c in convos:
        last = (
            db.query(AdvisorMessage)
            .filter(AdvisorMessage.conversation_id == c.id, AdvisorMessage.role == "assistant")
            .order_by(AdvisorMessage.id.desc())
            .first()
        )
        preview = " ".join(last.content.split())[:140] if last else None
        out.append(ConversationSummary(id=str(c.id), title=c.title, preview=preview, updated_at=_iso(c.updated_at)))
    return out


@router.get("/conversations/{conversation_id}", response_model=ConversationDetail)
def get_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conversation = _own_conversation(db, conversation_id, str(current_user.id))
    if conversation is None:
        raise HTTPException(status_code=404, detail="Chat not found.")
    rows = (
        db.query(AdvisorMessage)
        .filter(AdvisorMessage.conversation_id == conversation.id)
        .order_by(AdvisorMessage.id.asc())
        .all()
    )
    return ConversationDetail(
        id=str(conversation.id),
        title=conversation.title,
        messages=[StoredMessageOut(id=r.id, role=r.role, content=r.content, created_at=_iso(r.created_at)) for r in rows],
    )


@router.delete("/conversations/{conversation_id}", status_code=204)
def delete_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conversation = _own_conversation(db, conversation_id, str(current_user.id))
    if conversation is None:
        raise HTTPException(status_code=404, detail="Chat not found.")
    db.query(AdvisorMessage).filter(AdvisorMessage.conversation_id == conversation.id).delete()
    db.delete(conversation)
    db.commit()
    return Response(status_code=204)
