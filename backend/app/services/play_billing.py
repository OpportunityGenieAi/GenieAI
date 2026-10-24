"""Checks Google Play subscriptions and decides who has Premium."""
import json
import logging
import re
import threading
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional
from urllib.parse import quote

import httpx
from sqlalchemy.orm import Session

from app.config import settings
from app.models import User
from app.models_billing import PlaySubscription

logger = logging.getLogger(__name__)

_SCOPE = "https://www.googleapis.com/auth/androidpublisher"
_API = "https://androidpublisher.googleapis.com/androidpublisher/v3/applications"

# States in which the student has paid for the current period.
ENTITLED_STATES = {
    "SUBSCRIPTION_STATE_ACTIVE",
    "SUBSCRIPTION_STATE_IN_GRACE_PERIOD",
    "SUBSCRIPTION_STATE_CANCELED",  # cancelled, but paid up until expires_at
}

_creds = None
_creds_lock = threading.Lock()


class PlayBillingError(Exception):
    def __init__(self, message: str, status: int = 502):
        super().__init__(message)
        self.message = message
        self.status = status


def _valid_uuid(value: str) -> bool:
    try:
        uuid.UUID(str(value))
        return True
    except ValueError:
        return False


def _access_token() -> str:
    global _creds
    raw = (settings.GOOGLE_PLAY_SERVICE_ACCOUNT_JSON or "").strip()
    if not raw:
        raise PlayBillingError("Subscriptions aren't configured on the server yet.", 503)
    try:
        import google.auth.transport.requests
        from google.oauth2 import service_account

        with _creds_lock:
            if _creds is None:
                _creds = service_account.Credentials.from_service_account_info(json.loads(raw), scopes=[_SCOPE])
            if not _creds.valid:
                _creds.refresh(google.auth.transport.requests.Request())
            return _creds.token
    except Exception:
        logger.exception("Could not get a Google access token")
        raise PlayBillingError("Couldn't reach Google Play just now — try again.", 502)


def _parse_time(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    text = re.sub(r"(\.\d{6})\d+", r"\1", value.strip().replace("Z", "+00:00"))
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is not None:
        parsed = parsed.astimezone(timezone.utc).replace(tzinfo=None)
    return parsed


def fetch_subscription(purchase_token: str) -> dict:
    """Asks Google what it knows about this purchase token."""
    url = (
        f"{_API}/{settings.GOOGLE_PLAY_PACKAGE_NAME}"
        f"/purchases/subscriptionsv2/tokens/{quote(purchase_token, safe='')}"
    )
    try:
        with httpx.Client(timeout=20.0) as client:
            response = client.get(url, headers={"Authorization": f"Bearer {_access_token()}"})
    except httpx.HTTPError as exc:
        logger.warning("Play API request failed: %s", exc)
        raise PlayBillingError("Couldn't reach Google Play just now — try again.", 502)
    if response.status_code == 200:
        return response.json()
    if response.status_code in (400, 404, 410):
        logger.warning("Play rejected the purchase token (%s): %s", response.status_code, response.text[:300])
        raise PlayBillingError("That purchase couldn't be verified.", 400)
    logger.error("Play API error %s: %s", response.status_code, response.text[:500])
    raise PlayBillingError("Couldn't verify the purchase just now — try again.", 502)


def _acknowledge(product_id: str, token: str) -> None:
    """Play refunds purchases that are not acknowledged within 3 days, so do it right after verifying."""
    url = (
        f"{_API}/{settings.GOOGLE_PLAY_PACKAGE_NAME}/purchases/subscriptions/"
        f"{quote(product_id, safe='')}/tokens/{quote(token, safe='')}:acknowledge"
    )
    try:
        with httpx.Client(timeout=20.0) as client:
            response = client.post(
                url,
                headers={"Authorization": f"Bearer {_access_token()}", "content-type": "application/json"},
                json={},
            )
        if response.status_code not in (200, 204):
            logger.warning("Play acknowledge returned %s: %s", response.status_code, response.text[:300])
    except Exception:
        logger.warning("Play acknowledge failed", exc_info=True)


def is_entitled(row: PlaySubscription) -> bool:
    return bool(row.state in ENTITLED_STATES and row.expires_at and row.expires_at > datetime.utcnow())


def apply_subscription(
    db: Session, token: str, data: dict, user_id: Optional[str] = None
) -> Optional[PlaySubscription]:
    """Saves what Google says about this purchase. Returns None if it can't be tied to an account."""
    items = data.get("lineItems") or []
    item = next((i for i in items if i.get("productId") == settings.GOOGLE_PLAY_PRODUCT_ID), None)
    if item is None:
        raise PlayBillingError("That purchase is for a different product.", 400)

    owner = ((data.get("externalAccountIdentifiers") or {}).get("obfuscatedExternalAccountId") or "").strip()
    row = db.query(PlaySubscription).filter(PlaySubscription.purchase_token == token).first()

    if row is None:
        if user_id and owner and owner != user_id:
            raise PlayBillingError("This purchase belongs to a different account.", 409)
        link_to = user_id or owner
        if not link_to or not _valid_uuid(link_to) or not db.query(User.id).filter(User.id == link_to).first():
            logger.warning("Play purchase could not be linked to an account")
            return None
        row = PlaySubscription(
            user_id=link_to, purchase_token=token, product_id=settings.GOOGLE_PLAY_PRODUCT_ID, state=""
        )
        db.add(row)
    elif user_id and str(row.user_id) != user_id:
        raise PlayBillingError("This subscription is already linked to another account.", 409)

    row.state = data.get("subscriptionState") or ""
    row.expires_at = _parse_time(item.get("expiryTime"))
    row.auto_renewing = bool((item.get("autoRenewingPlan") or {}).get("autoRenewEnabled"))
    row.is_test = "testPurchase" in data
    row.order_id = data.get("latestOrderId")
    row.updated_at = datetime.utcnow()
    db.flush()

    user = db.query(User).filter(User.id == row.user_id).first()
    if user:
        rows = db.query(PlaySubscription).filter(PlaySubscription.user_id == row.user_id).all()
        user.subscription_tier = "premium" if any(is_entitled(r) for r in rows) else "free"
    db.commit()

    if is_entitled(row) and data.get("acknowledgementState") == "ACKNOWLEDGEMENT_STATE_PENDING":
        _acknowledge(settings.GOOGLE_PLAY_PRODUCT_ID, token)
    return row


def is_premium_user(db: Session, user: User) -> bool:
    """True if the student has paid (or is an admin). Ignores the gating date."""
    if user.is_admin:
        return True
    rows = db.query(PlaySubscription).filter(PlaySubscription.user_id == str(user.id)).all()
    if rows:
        return any(is_entitled(r) for r in rows)
    return user.subscription_tier == "premium"


def _gating_start() -> Optional[datetime]:
    """When Premium starts being enforced (UTC). Empty or invalid means it is not enforced yet."""
    raw = (settings.PREMIUM_GATING_STARTS_AT or "").strip()
    if not raw:
        return None
    try:
        start = datetime.fromisoformat(raw)
    except ValueError:
        logger.error("PREMIUM_GATING_STARTS_AT is not a valid date: %r", raw)
        return None
    if start.tzinfo is not None:
        start = start.astimezone(timezone.utc).replace(tzinfo=None)
    return start


def gating_active() -> bool:
    start = _gating_start()
    return bool(start and datetime.utcnow() >= start)


def grace_until_for(user: User) -> Optional[datetime]:
    """Accounts created before Premium started keep full access for PREMIUM_GRACE_DAYS."""
    start = _gating_start()
    if not start:
        return None
    if user.created_at and user.created_at >= start:
        return None
    return start + timedelta(days=settings.PREMIUM_GRACE_DAYS)


def has_access(db: Session, user: User) -> bool:
    """What the premium features check: open to all until Premium starts, then paid users and grace-period accounts."""
    if not gating_active():
        return True
    if is_premium_user(db, user):
        return True
    grace = grace_until_for(user)
    return bool(grace and datetime.utcnow() < grace)
