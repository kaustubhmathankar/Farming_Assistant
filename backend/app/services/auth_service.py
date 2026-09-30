from datetime import timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import RevokedToken, User
from app.services.farmer_service import create_farmer, serialize_farmer
from app.services.security_service import create_access_token, hash_password, verify_password


def public_user(user: User) -> dict:
    return {
        "id": user.id,
        "email": user.email,
        "role": user.role,
        "is_active": user.is_active,
        "farmer": serialize_farmer(user.farmer) if user.farmer else None,
    }


def register(db: Session, payload):
    email = str(payload.email).lower().strip()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=409, detail="An account with this email already exists")

    farmer = create_farmer(
        db,
        full_name=payload.full_name,
        language=payload.language,
        state=payload.state,
        district=payload.district,
        village=payload.village,
    )
    user = User(email=email, farmer_id=farmer.id, password_hash=hash_password(payload.password), role="farmer")
    db.add(user)
    db.commit()
    db.refresh(user)
    token, _, _ = create_access_token(user.id, farmer.id, user.role, user.token_version)
    return user, token, settings.access_token_expire_minutes * 60


def login(db: Session, email: str, password: str):
    normalized = str(email).lower().strip()
    user = db.scalar(select(User).where(User.email == normalized))
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Your account has been disabled")
    if not user.farmer:
        raise HTTPException(status_code=500, detail="Farmer profile is missing")
    token, _, _ = create_access_token(user.id, user.farmer.id, user.role, user.token_version)
    return user, token, settings.access_token_expire_minutes * 60


def logout(db: Session, jti: str, expires_at) -> None:
    expiry = expires_at.astimezone(timezone.utc).replace(tzinfo=None) if expires_at.tzinfo else expires_at
    db.add(RevokedToken(jti=jti, expires_at=expiry))
    db.commit()


def change_password(db: Session, user: User, current_password: str, new_password: str) -> None:
    if not verify_password(current_password, user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    if current_password == new_password:
        raise HTTPException(status_code=400, detail="New password must be different")
    user.password_hash = hash_password(new_password)
    user.token_version += 1
    db.commit()
