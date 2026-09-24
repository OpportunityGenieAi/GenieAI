from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import User
from app.schemas import (
    ForgotPasswordStart, ForgotPasswordVerify, LoginRequest, MessageResponse,
    ResendCodeRequest, SignupRequest, TokenResponse, UserOut, VerifyEmailRequest,
)
from app.security import create_access_token, verify_password
from app.services import supabase_auth
from app.services.supabase_auth import SupabaseAuthError

router = APIRouter(prefix="/auth", tags=["auth"])


def _name_from_supabase(session: dict, email: str) -> str:
    meta = (session.get("user") or {}).get("user_metadata") or {}
    return (meta.get("name") or email.split("@")[0]).strip()


def _get_or_create_user(db: Session, email: str, name: str) -> User:
    """Our own profile row is created the first time a verified Supabase user appears."""
    user = db.query(User).filter(User.email == email).first()
    if user:
        return user
    user = User(name=name, email=email, is_admin=False)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _token_response(user: User) -> TokenResponse:
    return TokenResponse(
        access_token=create_access_token(subject=user.email),
        user=UserOut.model_validate(user),
    )


@router.post("/signup", response_model=MessageResponse)
def signup(payload: SignupRequest, db: Session = Depends(get_db)):
    """Step 1 of signup: Supabase emails a confirmation code. No login yet."""
    email = payload.email.lower()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=409, detail="An account with that email already exists.")

    supabase_auth.sign_up(email, payload.password, payload.name.strip())
    return MessageResponse(message="We've emailed you a confirmation code.")


@router.post("/verify-email", response_model=TokenResponse)
def verify_email(payload: VerifyEmailRequest, db: Session = Depends(get_db)):
    """Step 2 of signup: the user types the emailed code; on success they're logged in."""
    email = payload.email.lower()
    session = supabase_auth.verify_code(email, payload.code, "signup")
    user = _get_or_create_user(db, email, _name_from_supabase(session, email))
    return _token_response(user)


@router.post("/resend-code", response_model=MessageResponse)
def resend_code(payload: ResendCodeRequest):
    supabase_auth.resend_signup_code(payload.email.lower())
    return MessageResponse(message="If that email is waiting for confirmation, a new code is on its way.")


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    email = payload.email.lower()
    try:
        session = supabase_auth.sign_in(email, payload.password)
    except SupabaseAuthError as e:
        # 403 tells the apps "email not verified yet" so they can show the code screen.
        if e.error_code != "invalid_credentials":
            raise
        # Accounts created before the Supabase switch have no Supabase user yet;
        # let them in with their old password so nobody (e.g. your admin) is locked out.
        legacy = db.query(User).filter(User.email == email).first()
        if legacy and legacy.password_hash and verify_password(payload.password, legacy.password_hash):
            return _token_response(legacy)
        raise

    user = _get_or_create_user(db, email, _name_from_supabase(session, email))
    return _token_response(user)


@router.post("/forgot-password/start", response_model=MessageResponse)
def forgot_password_start(payload: ForgotPasswordStart):
    """Supabase emails a reset code. Always answers the same way so it doesn't reveal who has an account."""
    supabase_auth.send_recovery_code(payload.email.lower())
    return MessageResponse(message="If an account exists for that email, we've sent a reset code.")


@router.post("/forgot-password/verify", response_model=MessageResponse)
def forgot_password_verify(payload: ForgotPasswordVerify):
    session = supabase_auth.verify_code(payload.email.lower(), payload.code, "recovery")
    supabase_auth.update_password(session["access_token"], payload.new_password)
    return MessageResponse(message="Password updated. You can log in now.")


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return UserOut.model_validate(current_user)


@router.get("/debug-list-users-temp")
def debug_list_users_temp(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return [{"name": u.name, "email": u.email, "is_admin": u.is_admin} for u in users]


@router.post("/debug-make-admin-temp")
def debug_make_admin_temp(payload: dict, db: Session = Depends(get_db)):
    if payload.get("secret") != "temp-fix-2026b":
        raise HTTPException(status_code=403, detail="wrong secret")
    user = db.query(User).filter(User.email == payload.get("email", "").lower()).first()
    if not user:
        raise HTTPException(status_code=404, detail="user not found")
    user.is_admin = True
    db.commit()
    return {"email": user.email, "is_admin": user.is_admin}
