"""
Admin-editable configuration.

Design: any setting can be written by an admin. A fixed allow-list of
"public" keys (ad unit IDs — safe to expose, meaningless without the
AdMob app itself) can be read by anyone, since the app needs them before
a user necessarily logs in. Everything else (API keys, secrets) requires
admin auth to read, and is never sent to the mobile app at all — those
exist purely so an admin can update a value here instead of touching
Render's dashboard, for services the *backend* calls server-side
(e.g. swapping in a real Stripe key when ready).
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_admin
from app.models import AppSetting, User
from app.schemas import AppSettingIn, AppSettingOut

router = APIRouter(prefix="/settings", tags=["settings"])

PUBLIC_KEYS = {
    "admob_banner_unit_id_ios",
    "admob_banner_unit_id_android",
    "admob_interstitial_unit_id_ios",
    "admob_interstitial_unit_id_android",
}

# Keys an admin is allowed to manage through this API at all (protects
# against accidentally — or maliciously — writing arbitrary keys).
MANAGED_KEYS = PUBLIC_KEYS | {
    "anthropic_api_key_override",
    "stripe_secret_key_override",
}


@router.get("/public", response_model=list[AppSettingOut])
def get_public_settings(db: Session = Depends(get_db)):
    """No auth required — the app needs these (e.g. ad unit IDs) before login."""
    rows = db.query(AppSetting).filter(AppSetting.key.in_(PUBLIC_KEYS)).all()
    return [AppSettingOut.model_validate(r) for r in rows]


@router.get("", response_model=list[AppSettingOut])
def list_all_settings(db: Session = Depends(get_db), _admin: User = Depends(get_current_admin)):
    rows = db.query(AppSetting).filter(AppSetting.key.in_(MANAGED_KEYS)).all()
    found = {r.key for r in rows}
    result = [AppSettingOut.model_validate(r) for r in rows]
    # include unset managed keys as empty, so the admin UI can show every field
    for k in MANAGED_KEYS - found:
        result.append(AppSettingOut(key=k, value=None))
    return result


@router.put("/{key}", response_model=AppSettingOut)
def set_setting(key: str, payload: AppSettingIn, db: Session = Depends(get_db), _admin: User = Depends(get_current_admin)):
    if key not in MANAGED_KEYS:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=f"'{key}' is not a manageable setting.")
    row = db.query(AppSetting).filter(AppSetting.key == key).first()
    if not row:
        row = AppSetting(key=key)
        db.add(row)
    row.value = payload.value
    db.commit()
    db.refresh(row)
    return AppSettingOut.model_validate(row)
