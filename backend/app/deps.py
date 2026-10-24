from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.security import decode_access_token

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    email = decode_access_token(credentials.credentials)
    if not email:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


def get_current_admin(user: User = Depends(get_current_user)) -> User:
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User | None:
    if credentials is None:
        return None
    email = decode_access_token(credentials.credentials)
    if not email:
        return None
    return db.query(User).filter(User.email == email).first()


def require_premium(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> User:
    """Premium-only endpoints. Open to everyone until PREMIUM_GATING_STARTS_AT, then paid users and the grace period."""
    from app.services.play_billing import has_access

    if not has_access(db, user):
        raise HTTPException(status_code=402, detail="This feature is part of OpportunityGenie Premium.")
    return user
