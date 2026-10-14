from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import User
from app.models_push import PushToken
from app.services.push import send_test

router = APIRouter(prefix="/notifications", tags=["notifications"])


class TokenIn(BaseModel):
    token: str
    platform: Optional[str] = None


@router.post("/token", status_code=204)
def register_token(
    payload: TokenIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    token = payload.token.strip()
    if not token.startswith(("ExponentPushToken[", "ExpoPushToken[")):
        raise HTTPException(status_code=400, detail="That isn't a valid push token.")
    row = db.query(PushToken).filter(PushToken.token == token).first()
    if row:
        row.user_id = str(current_user.id)  # a device that switches accounts follows the new login
        row.enabled = True
        row.platform = payload.platform
        row.updated_at = datetime.utcnow()
    else:
        db.add(PushToken(user_id=str(current_user.id), token=token, platform=payload.platform))
    db.commit()
    return None


@router.post("/token/disable", status_code=204)
def disable_token(
    payload: TokenIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    row = (
        db.query(PushToken)
        .filter(PushToken.token == payload.token.strip(), PushToken.user_id == str(current_user.id))
        .first()
    )
    if row:
        row.enabled = False
        row.updated_at = datetime.utcnow()
        db.commit()
    return None


@router.post("/test")
def test_notification(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return {"sent": send_test(db, str(current_user.id))}
