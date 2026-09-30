from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import CurrentAuth, get_current_auth
from app.schemas import FarmerOut, FarmerUpdate
from app.services.farmer_service import get_farmer, serialize_farmer, update_farmer

router = APIRouter(prefix="/farmers", tags=["Farmer Profile"])


@router.get("/me", response_model=FarmerOut)
def get_my_profile(auth: CurrentAuth = Depends(get_current_auth), db: Session = Depends(get_db)):
    farmer = get_farmer(db, auth.farmer_id)
    if not farmer:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Farmer profile not found")
    return serialize_farmer(farmer)


@router.put("/me", response_model=FarmerOut)
def update_my_profile(payload: FarmerUpdate, auth: CurrentAuth = Depends(get_current_auth), db: Session = Depends(get_db)):
    farmer = get_farmer(db, auth.farmer_id)
    if not farmer:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Farmer profile not found")
    update_farmer(db, farmer, payload.model_dump())
    db.commit()
    db.refresh(farmer)
    return serialize_farmer(farmer)
