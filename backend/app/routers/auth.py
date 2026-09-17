from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import User
from app.schemas import (
    ForgotPasswordStart, ForgotPasswordStartResponse, ForgotPasswordVerify,
    LoginRequest, SignupRequest, TokenResponse, UserOut,
)
from app.security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=TokenResponse)
def signup(payload: SignupRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email.lower()).first()
    if existing:
        raise HTTPException(status_code=409, detail="An account with that email already exists.")

    user = User(
        name=payload.name.strip(),
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
        security_question=payload.security_question,
        security_answer_hash=hash_password(payload.security_answer.strip().lower()),
        is_admin=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(subject=user.email)
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="That email and password don't match our records.")

    token = create_access_token(subject=user.email)
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))


@router.post("/forgot-password/start", response_model=ForgotPasswordStartResponse)
def forgot_password_start(payload: ForgotPasswordStart, db: Session = Depends(get_db)):
    """
    NOTE — production hardening: a security question is a weak recovery
    channel. Before real launch, add an emailed reset-token flow (e.g. via
    SendGrid/SES): generate a short-lived signed token, email a reset link,
    and verify the token in forgot-password/verify instead of (or in
    addition to) the security answer below.
    """
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if not user:
        raise HTTPException(status_code=404, detail="We couldn't find an account with that email.")
    return ForgotPasswordStartResponse(security_question=user.security_question)


@router.post("/forgot-password/verify", response_model=UserOut)
def forgot_password_verify(payload: ForgotPasswordVerify, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if not user or not verify_password(payload.security_answer.strip().lower(), user.security_answer_hash):
        raise HTTPException(status_code=401, detail="That answer doesn't match what we have on file.")

    user.password_hash = hash_password(payload.new_password)
    db.commit()
    db.refresh(user)
    return UserOut.model_validate(user)


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return UserOut.model_validate(current_user)
