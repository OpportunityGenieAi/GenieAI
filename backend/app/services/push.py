"""Sends push notifications through Expo's push service."""
import logging

import httpx

from app.database import SessionLocal
from app.models import AcademicProfile, GpaProfile, Scholarship
from app.models_push import PushToken
from app.services.match_engine import compute_match_score

logger = logging.getLogger(__name__)

EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"
MIN_FIT = 50   # students with a saved profile only get scholarships that fit at least this much
BATCH_SIZE = 100


def _send_batches(db, messages: list[dict]) -> int:
    """Posts messages to Expo in batches and removes tokens Expo says are dead."""
    dead: list[str] = []
    sent = 0
    with httpx.Client(timeout=20.0) as client:
        for i in range(0, len(messages), BATCH_SIZE):
            chunk = messages[i:i + BATCH_SIZE]
            try:
                resp = client.post(
                    EXPO_PUSH_URL,
                    json=chunk,
                    headers={"accept": "application/json", "content-type": "application/json"},
                )
            except httpx.HTTPError as exc:
                logger.warning("Expo push request failed: %s", exc)
                continue
            if resp.status_code != 200:
                logger.warning("Expo push error %s: %s", resp.status_code, resp.text[:300])
                continue
            for msg, ticket in zip(chunk, resp.json().get("data", [])):
                if ticket.get("status") == "ok":
                    sent += 1
                elif (ticket.get("details") or {}).get("error") == "DeviceNotRegistered":
                    dead.append(msg["to"])
    if dead:
        db.query(PushToken).filter(PushToken.token.in_(dead)).delete(synchronize_session=False)
        db.commit()
    return sent


def notify_new_scholarship(scholarship_id: str) -> None:
    """Runs in the background after an admin adds a scholarship."""
    db = SessionLocal()
    try:
        s = db.query(Scholarship).filter(Scholarship.id == scholarship_id).first()
        if not s:
            return
        rows = db.query(PushToken).filter(PushToken.enabled.is_(True)).all()
        if not rows:
            return

        user_ids = list({str(r.user_id) for r in rows})
        gpas = {str(g.user_id): g for g in db.query(GpaProfile).filter(GpaProfile.user_id.in_(user_ids)).all()}
        acads = {str(a.user_id): a for a in db.query(AcademicProfile).filter(AcademicProfile.user_id.in_(user_ids)).all()}

        title = f"New scholarship: {s.name}"[:100]
        base = " · ".join(x for x in (getattr(s, "provider", None), getattr(s, "country", None), getattr(s, "level", None)) if x)
        messages: list[dict] = []
        for r in rows:
            uid = str(r.user_id)
            g, a = gpas.get(uid), acads.get(uid)
            if g and a:
                try:
                    score = int(round(compute_match_score(s, g, a)["score"]))
                except Exception:
                    continue
                if score < MIN_FIT:
                    continue
                body = f"{score}% match with your profile · {base}"
            else:
                body = base or "Tap to see the details."
            messages.append({
                "to": r.token,
                "title": title,
                "body": body[:178],
                "sound": "default",
                "channelId": "default",
                "data": {"type": "scholarship", "scholarshipId": str(s.id)},
            })

        sent = _send_batches(db, messages) if messages else 0
        logger.info("New-scholarship push for %s: %s of %s tokens notified", s.id, sent, len(rows))
    except Exception:
        logger.exception("notify_new_scholarship failed")
    finally:
        db.close()


def send_test(db, user_id: str) -> int:
    rows = db.query(PushToken).filter(PushToken.user_id == user_id, PushToken.enabled.is_(True)).all()
    messages = [
        {
            "to": r.token,
            "title": "Notifications are on",
            "body": "You'll get a message here when a new scholarship is added.",
            "sound": "default",
            "channelId": "default",
            "data": {"type": "test"},
        }
        for r in rows
    ]
    return _send_batches(db, messages) if messages else 0
