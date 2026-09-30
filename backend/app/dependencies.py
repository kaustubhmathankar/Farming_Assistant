from dataclasses import dataclass
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import RevokedToken, User, utcnow_naive
from app.services.security_service import InvalidTokenError, decode_access_token


bearer = HTTPBearer(auto_error=False)


@dataclass
class CurrentAuth:
    user: User
    farmer_id: str
    role: str
    jti: str



def get_current_auth(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    db: Session = Depends(get_db),
) -> CurrentAuth:
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required", headers={"WWW-Authenticate": "Bearer"})

    try:
        payload = decode_access_token(credentials.credentials)
    except InvalidTokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc), headers={"WWW-Authenticate": "Bearer"}) from exc

    jti = str(payload["jti"])
    revoked = db.scalar(select(RevokedToken).where(RevokedToken.jti == jti))
    if revoked:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session has been logged out")

    user = db.scalar(
        select(User)
        .options(joinedload(User.farmer))
        .where(User.id == str(payload["sub"]))
    )
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Account is inactive or unavailable")

    if user.token_version != int(payload["ver"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired. Please sign in again.")

    farmer_id = user.farmer.id if user.farmer else str(payload.get("farmer_id", ""))
    if not farmer_id:
        raise HTTPException(status_code=500, detail="Farmer profile is missing")

    return CurrentAuth(user=user, farmer_id=farmer_id, role=user.role, jti=jti)



def get_current_user(auth: CurrentAuth = Depends(get_current_auth)) -> User:
    return auth.user



def require_admin(auth: CurrentAuth = Depends(get_current_auth)) -> CurrentAuth:
    if auth.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return auth
