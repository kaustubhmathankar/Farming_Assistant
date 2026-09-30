import json
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Farmer
from app.services.language_service import normalize_language


def normalize_crops(crops: list[str] | None) -> list[str]:
    seen = []
    for crop in crops or []:
        value = " ".join(str(crop).strip().split())
        if value and value.lower() not in {x.lower() for x in seen}:
            seen.append(value[:80])
    return seen[:20]


def get_farmer(db: Session, farmer_id: str) -> Farmer | None:
    return db.scalar(select(Farmer).where(Farmer.id == farmer_id))


def create_farmer(
    db: Session,
    *,
    full_name: str,
    language: str,
    state: str = "",
    district: str = "",
    village: str = "",
) -> Farmer:
    farmer = Farmer(
        full_name=full_name.strip(),
        language=normalize_language(language),
        state=state.strip(),
        district=district.strip(),
        village=village.strip(),
        crops_json="[]",
    )
    db.add(farmer)
    db.flush()
    return farmer


def update_farmer(db: Session, farmer: Farmer, data: dict) -> Farmer:
    for field in ["full_name", "state", "district", "village", "irrigation_type", "soil_type", "farming_type"]:
        if field in data and data[field] is not None:
            setattr(farmer, field, str(data[field]).strip())
    farmer.language = normalize_language(data.get("language"))
    farmer.crops_json = json.dumps(normalize_crops(data.get("crops")), ensure_ascii=False)
    farmer.land_size_acres = data.get("land_size_acres")
    return farmer


def farmer_context(farmer: Farmer) -> str:
    crops = json.loads(farmer.crops_json or "[]")
    parts = [f"Farmer: {farmer.full_name}", f"Preferred language: {farmer.language}"]
    if farmer.state or farmer.district or farmer.village:
        parts.append(f"Location: {farmer.village}, {farmer.district}, {farmer.state}".strip(" ,"))
    if crops:
        parts.append(f"Common crops: {', '.join(crops)}")
    if farmer.land_size_acres is not None:
        parts.append(f"Land size: {farmer.land_size_acres} acres")
    if farmer.irrigation_type:
        parts.append(f"Irrigation: {farmer.irrigation_type}")
    if farmer.soil_type:
        parts.append(f"Soil: {farmer.soil_type}")
    if farmer.farming_type:
        parts.append(f"Farming type: {farmer.farming_type}")
    return "\n".join(parts)


def serialize_farmer(farmer: Farmer) -> dict:
    return {
        "id": farmer.id,
        "full_name": farmer.full_name,
        "language": farmer.language,
        "state": farmer.state,
        "district": farmer.district,
        "village": farmer.village,
        "crops": json.loads(farmer.crops_json or "[]"),
        "land_size_acres": farmer.land_size_acres,
        "irrigation_type": farmer.irrigation_type,
        "soil_type": farmer.soil_type,
        "farming_type": farmer.farming_type,
    }
