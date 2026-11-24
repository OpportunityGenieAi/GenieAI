"""Paid consultations: verify the Google Play purchase, collect the form + documents, email the team."""
import logging
import secrets
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from urllib.parse import quote

import httpx
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.deps import get_current_user
from app.models import User
from app.models_consultation import Consultation, ConsultationFile
from app.services import mailer
from app.services.consult_utils import MAX_FILES, PRODUCTS, clean, decode_upload, valid_email
from app.services.play_billing import _API, PlayBillingError, _access_token

import os

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/consultations", tags=["consultations"])

NOTIFY_TO = os.environ.get("CONSULT_NOTIFY_EMAIL", "info@opportunitygenie.org")
PAGE = Path(__file__).resolve().parent.parent / "pages" / "consult_upload.html"


# ---------- schemas ----------
class VerifyIn(BaseModel):
    purchase_token: str
    product_id: str


class FormIn(BaseModel):
    full_name: str
    email: str
    country: str
    education_level: str
    study_interest: str
    applied_scholarships: str = ""
    academic_summary: str
    availability: str = ""
    notes: str = ""


class UploadIn(BaseModel):
    filename: str
    data: str  # base64


def _files(db: Session, cid: str) -> List[ConsultationFile]:
    return db.query(ConsultationFile).filter(ConsultationFile.consultation_id == cid).order_by(ConsultationFile.created_at).all()


def _out(db: Session, c: Consultation) -> dict:
    return {
        "id": c.id,
        "minutes": c.minutes,
        "status": c.status,
        "upload_token": c.upload_token,
        "created_at": c.created_at.isoformat() if c.created_at else None,
        "files": [{"id": f.id, "filename": f.filename, "size": f.size} for f in _files(db, c.id)],
    }


# ---------- Google Play (one-time product) ----------
def _verify_with_google(product_id: str, token: str) -> dict:
    url = (
        f"{_API}/{settings.GOOGLE_PLAY_PACKAGE_NAME}/purchases/products/"
        f"{quote(product_id, safe='')}/tokens/{quote(token, safe='')}"
    )
    try:
        with httpx.Client(timeout=20.0) as client:
            r = client.get(url, headers={"Authorization": f"Bearer {_access_token()}"})
    except httpx.HTTPError as exc:
        logger.warning("Play API request failed: %s", exc)
        raise PlayBillingError("Couldn't reach Google Play just now — try again.", 502)
    if r.status_code == 200:
        return r.json()
    if r.status_code in (400, 404, 410):
        logger.warning("Play rejected consultation token (%s): %s", r.status_code, r.text[:300])
        raise PlayBillingError("That purchase couldn't be verified.", 400)
    logger.error("Play API error %s: %s", r.status_code, r.text[:500])
    raise PlayBillingError("Couldn't verify the purchase just now — try again.", 502)


def _acknowledge(product_id: str, token: str) -> None:
    url = (
        f"{_API}/{settings.GOOGLE_PLAY_PACKAGE_NAME}/purchases/products/"
        f"{quote(product_id, safe='')}/tokens/{quote(token, safe='')}:acknowledge"
    )
    try:
        with httpx.Client(timeout=20.0) as client:
            r = client.post(url, json={}, headers={"Authorization": f"Bearer {_access_token()}"})
        if r.status_code >= 300 and "already" not in r.text.lower():
            logger.warning("Consultation acknowledge failed (%s): %s", r.status_code, r.text[:200])
    except Exception:
        logger.exception("Consultation acknowledge failed")


# ---------- app endpoints ----------
@router.post("/verify")
def verify(payload: VerifyIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    token = payload.purchase_token.strip()
    product = payload.product_id.strip()
    if not token or len(token) > 2000 or product not in PRODUCTS:
        raise HTTPException(status_code=400, detail="That purchase isn't recognised.")

    existing = db.query(Consultation).filter(Consultation.purchase_token == token).first()
    if existing:
        if existing.user_id != str(user.id):
            raise HTTPException(status_code=409, detail="That purchase belongs to another account.")
        return _out(db, existing)

    try:
        data = _verify_with_google(product, token)
    except PlayBillingError as e:
        raise HTTPException(status_code=e.status, detail=e.message)

    if data.get("purchaseState") == 2:
        raise HTTPException(status_code=402, detail="Your payment is still pending. Try again once Google confirms it.")
    if data.get("purchaseState") != 0:
        raise HTTPException(status_code=400, detail="That purchase was cancelled or refunded.")

    if data.get("acknowledgementState") != 1:
        _acknowledge(product, token)

    c = Consultation(
        user_id=str(user.id),
        product_id=product,
        minutes=PRODUCTS[product],
        purchase_token=token,
        order_id=data.get("orderId"),
        upload_token=secrets.token_urlsafe(24),
        status="paid",
        is_test=data.get("purchaseType") == 0,
        email=user.email,
        full_name=user.name,
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return _out(db, c)


@router.get("/mine")
def mine(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = (
        db.query(Consultation)
        .filter(Consultation.user_id == str(user.id))
        .order_by(Consultation.created_at.desc())
        .limit(20)
        .all()
    )
    return [_out(db, c) for c in rows]


def _owned(db: Session, cid: str, user: User) -> Consultation:
    c = db.query(Consultation).filter(Consultation.id == cid, Consultation.user_id == str(user.id)).first()
    if not c:
        raise HTTPException(status_code=404, detail="Booking not found.")
    return c


@router.post("/{cid}/submit")
def submit(cid: str, form: FormIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    c = _owned(db, cid, user)
    if c.status == "submitted":
        raise HTTPException(status_code=409, detail="This booking form was already sent.")

    c.full_name = clean(form.full_name, 120)
    c.email = clean(form.email, 254).lower()
    c.country = clean(form.country, 80)
    c.education_level = clean(form.education_level, 60)
    c.study_interest = clean(form.study_interest, 200)
    c.applied_scholarships = clean(form.applied_scholarships, 1500)
    c.academic_summary = clean(form.academic_summary, 2000)
    c.availability = clean(form.availability, 600)
    c.notes = clean(form.notes, 1500)

    missing = [n for n, v in [("name", c.full_name), ("country", c.country), ("education level", c.education_level),
                              ("what you want to study", c.study_interest), ("academic background", c.academic_summary)] if not v]
    if missing:
        raise HTTPException(status_code=400, detail="Please fill in: " + ", ".join(missing) + ".")
    if not valid_email(c.email):
        raise HTTPException(status_code=400, detail="Please enter a valid email address.")

    c.status = "submitted"
    c.submitted_at = datetime.utcnow()
    db.commit()  # saved first, so nothing is lost if email fails

    files = _files(db, c.id)
    body = (
        f"NEW CONSULTATION BOOKING ({c.minutes} minutes, paid via Google Play)\n"
        f"Order: {c.order_id or '-'}{'  [TEST PURCHASE]' if c.is_test else ''}\n\n"
        f"Name: {c.full_name}\nEmail: {c.email}\nCountry of origin: {c.country}\n"
        f"Current level of education: {c.education_level}\nWants to study: {c.study_interest}\n\n"
        f"Scholarships applied for so far:\n{c.applied_scholarships or '-'}\n\n"
        f"Current academic background:\n{c.academic_summary}\n\n"
        f"Availability:\n{c.availability or '-'}\n\nNotes:\n{c.notes or '-'}\n\n"
        f"Documents attached: {', '.join(f.filename for f in files) or 'none'}\n"
        f"Booking id: {c.id}\n"
    )
    sent = mailer.send_mail(
        [NOTIFY_TO], f"Consultation booking - {c.full_name} ({c.minutes} min)", body,
        attachments=[(f.filename, f.content_type, bytes(f.data)) for f in files], reply_to=c.email,
    )
    mailer.send_mail(
        [c.email],
        "We received your consultation request - OpportunityGenie",
        f"Hi {c.full_name.split(' ')[0]},\n\nThank you for booking a {c.minutes}-minute consultation with "
        "OpportunityGenie. We have received your details"
        f"{' and documents' if files else ''}.\n\n"
        "Next step: we will email you proposed meeting times within 1-2 working days. "
        "Please reply to confirm the time that suits you.\n\n"
        "If anything changes, just reply to this email.\n\nWarm regards,\nThe OpportunityGenie team\n",
    )
    if sent:
        c.email_sent = True
        db.commit()
    return {"ok": True, "email_sent": sent}


# ---------- document upload (opened in the phone's browser, secured by a one-time token) ----------
def _by_token(db: Session, token: str) -> Consultation:
    c = db.query(Consultation).filter(Consultation.upload_token == token).first()
    if not c or c.status == "submitted":
        raise HTTPException(status_code=404, detail="This upload link is no longer active.")
    return c


@router.get("/upload-page", response_class=HTMLResponse)
def upload_page():
    html = PAGE.read_text(encoding="utf-8")
    return HTMLResponse(html, headers={"Cache-Control": "no-store", "Referrer-Policy": "no-referrer"})


@router.get("/upload/{token}")
def upload_list(token: str, db: Session = Depends(get_db)):
    c = _by_token(db, token)
    return {"minutes": c.minutes, "files": [{"id": f.id, "filename": f.filename, "size": f.size} for f in _files(db, c.id)]}


@router.post("/upload/{token}")
def upload_add(token: str, payload: UploadIn, db: Session = Depends(get_db)):
    c = _by_token(db, token)
    if len(_files(db, c.id)) >= MAX_FILES:
        raise HTTPException(status_code=400, detail=f"You can attach up to {MAX_FILES} documents.")
    if len(payload.data) > 8 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Each file must be 5 MB or smaller.")
    parsed, err = decode_upload(payload.filename, payload.data)
    if err:
        raise HTTPException(status_code=400, detail=err)
    name, ctype, data = parsed
    f = ConsultationFile(consultation_id=c.id, filename=name, content_type=ctype, size=len(data), data=data)
    db.add(f)
    db.commit()
    return upload_list(token, db)


@router.delete("/upload/{token}/{file_id}")
def upload_remove(token: str, file_id: str, db: Session = Depends(get_db)):
    c = _by_token(db, token)
    f = db.query(ConsultationFile).filter(ConsultationFile.id == file_id, ConsultationFile.consultation_id == c.id).first()
    if f:
        db.delete(f)
        db.commit()
    return upload_list(token, db)


# ---------- admin ----------
@router.get("/admin/all")
def admin_all(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if not getattr(user, "is_admin", False):
        raise HTTPException(status_code=403, detail="Admins only.")
    rows = db.query(Consultation).order_by(Consultation.created_at.desc()).limit(200).all()
    return [
        {
            "id": c.id, "status": c.status, "minutes": c.minutes, "name": c.full_name, "email": c.email,
            "country": c.country, "level": c.education_level, "interest": c.study_interest,
            "email_sent": c.email_sent, "is_test": c.is_test,
            "submitted_at": c.submitted_at.isoformat() if c.submitted_at else None,
        }
        for c in rows
    ]
