import base64
import hmac
import json
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.deps import get_current_user
from app.models import User
from app.models_billing import PlaySubscription
from app.services.play_billing import (
    PlayBillingError,
    apply_subscription,
    fetch_subscription,
    gating_active,
    grace_until_for,
    has_access,
    is_entitled,
    is_premium_user,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/subscription", tags=["subscription"])


class VerifyIn(BaseModel):
    purchase_token: str
    product_id: Optional[str] = None


class StatusOut(BaseModel):
    premium: bool
    access: bool
    gating_enabled: bool
    product_id: str
    expires_at: Optional[datetime] = None
    auto_renewing: bool = False
    grace_until: Optional[datetime] = None


def _status(db: Session, user: User) -> StatusOut:
    rows = db.query(PlaySubscription).filter(PlaySubscription.user_id == str(user.id)).all()
    live = [r for r in rows if is_entitled(r)]
    best = max(live, key=lambda r: r.expires_at) if live else None
    premium = is_premium_user(db, user)
    grace = grace_until_for(user) if gating_active() and not premium else None
    if grace and grace <= datetime.utcnow():
        grace = None
    return StatusOut(
        premium=premium,
        access=has_access(db, user),
        gating_enabled=gating_active(),
        product_id=settings.GOOGLE_PLAY_PRODUCT_ID,
        expires_at=best.expires_at if best else None,
        auto_renewing=best.auto_renewing if best else False,
        grace_until=grace,
    )


@router.get("/status", response_model=StatusOut)
def subscription_status(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return _status(db, current_user)


@router.post("/verify", response_model=StatusOut)
def verify_purchase(
    payload: VerifyIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """The app calls this right after a purchase (and when restoring purchases)."""
    token = payload.purchase_token.strip()
    if not token or len(token) > 2000:
        raise HTTPException(status_code=400, detail="Missing purchase token.")
    try:
        data = fetch_subscription(token)
        apply_subscription(db, token, data, user_id=str(current_user.id))
    except PlayBillingError as e:
        raise HTTPException(status_code=e.status, detail=e.message)
    db.refresh(current_user)
    return _status(db, current_user)


@router.post("/rtdn")
def play_rtdn(
    payload: dict = Body(...),
    secret: str = Query(""),
    db: Session = Depends(get_db),
):
    """Google Play real-time notifications (renewals, cancellations, refunds) arrive here via Pub/Sub."""
    expected = settings.PLAY_RTDN_SECRET
    if not expected:
        raise HTTPException(status_code=503, detail="Not configured.")
    if not hmac.compare_digest(secret.encode("utf-8"), expected.encode("utf-8")):
        raise HTTPException(status_code=403, detail="Forbidden.")

    try:
        raw = base64.b64decode((payload.get("message") or {}).get("data") or "")
        event = json.loads(raw.decode("utf-8"))
    except ValueError:
        return {"ok": True}  # malformed: acknowledge so Pub/Sub does not keep retrying it

    package = event.get("packageName")
    if package and package != settings.GOOGLE_PLAY_PACKAGE_NAME:
        return {"ok": True}
    if "testNotification" in event:
        logger.info("Play test notification received")
        return {"ok": True}

    token = (event.get("subscriptionNotification") or {}).get("purchaseToken")
    if not token:
        voided = event.get("voidedPurchaseNotification") or {}
        if voided.get("productType") == 1:  # 1 = subscription
            token = voided.get("purchaseToken")
    if not token:
        return {"ok": True}

    try:
        data = fetch_subscription(token)
        apply_subscription(db, token, data)
    except PlayBillingError as e:
        if e.status >= 500:
            raise HTTPException(status_code=500, detail=e.message)  # Pub/Sub will retry
        logger.warning("Play notification skipped: %s", e.message)
    return {"ok": True}
