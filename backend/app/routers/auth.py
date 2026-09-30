from datetime import timezone, datetime
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.dependencies import CurrentAuth, get_current_auth, get_current_user
from app.schemas import LoginRequest, PasswordChangeRequest, RegisterRequest, TokenResponse
from app.services.auth_service import change_password, login, logout, public_user, register
from app.services.rate_limit import rate_limit

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register_user(request: Request, payload: RegisterRequest, db: Session = Depends(get_db), _=Depends(rate_limit(5, 60))):
    user, token, expires_in = register(db, payload)
    return {"access_token": token, "token_type": "bearer", "expires_in": expires_in, "user": public_user(user)}


@router.post("/login", response_model=TokenResponse)
async def login_user(request: Request, payload: LoginRequest, db: Session = Depends(get_db), _=Depends(rate_limit(5, 60))):
    user, token, expires_in = login(db, payload.email, payload.password)
    return {"access_token": token, "token_type": "bearer", "expires_in": expires_in, "user": public_user(user)}


@router.get("/me")
def me(user = Depends(get_current_user)):
    return public_user(user)


@router.post("/logout")
def logout_user(auth: CurrentAuth = Depends(get_current_auth), db: Session = Depends(get_db)):
    # Token expiry is already checked by get_current_auth; decode once to obtain exp.
    # Revocation blocks the token before its natural expiration.
    token_payload = {"jti": auth.jti}
    # Use a conservative one-day expiry for the revocation marker. It is cleaned up at startup.
    from datetime import timedelta
    expires = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    logout(db, auth.jti, expires)
    return {"message": "Logged out successfully"}


@router.post("/change-password")
def change_user_password(payload: PasswordChangeRequest, user = Depends(get_current_user), db: Session = Depends(get_db)):
    change_password(db, user, payload.current_password, payload.new_password)
    return {"message": "Password changed. Please sign in again on other devices."}
