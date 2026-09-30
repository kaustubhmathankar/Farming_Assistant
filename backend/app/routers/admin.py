from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import CurrentAuth, require_admin
from app.models import User
from app.schemas import AdminUserUpdate

router = APIRouter(prefix="/admin", tags=["Administration"])


@router.get("/dashboard")
def dashboard(auth: CurrentAuth = Depends(require_admin), db: Session = Depends(get_db)):
    return {
        "users": db.scalar(select(func.count(User.id))) or 0,
        "active_users": db.scalar(select(func.count(User.id)).where(User.is_active.is_(True))) or 0,
        "farmers": db.scalar(select(func.count(User.id)).where(User.role == "farmer")) or 0,
        "admins": db.scalar(select(func.count(User.id)).where(User.role == "admin")) or 0,
    }


@router.get("/users")
def users(auth: CurrentAuth = Depends(require_admin), db: Session = Depends(get_db)):
    rows = db.scalars(select(User).order_by(User.created_at.desc())).all()
    return [{"id": u.id, "email": u.email, "role": u.role, "is_active": u.is_active, "created_at": u.created_at.isoformat()} for u in rows]


@router.patch("/users/{user_id}")
def update_user(user_id: str, payload: AdminUserUpdate, auth: CurrentAuth = Depends(require_admin), db: Session = Depends(get_db)):
    target = db.get(User, user_id)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    if target.id == auth.user.id:
        if payload.role and payload.role != "admin":
            raise HTTPException(status_code=400, detail="You cannot remove your own admin role")
        if payload.is_active is False:
            raise HTTPException(status_code=400, detail="You cannot disable your own account")
    if payload.role is not None:
        if payload.role not in {"farmer", "admin"}:
            raise HTTPException(status_code=400, detail="Role must be farmer or admin")
        target.role = payload.role
        target.token_version += 1
    if payload.is_active is not None:
        target.is_active = payload.is_active
        if payload.is_active is False:
            target.token_version += 1
    db.commit()
    db.refresh(target)
    return {"id": target.id, "email": target.email, "role": target.role, "is_active": target.is_active}
