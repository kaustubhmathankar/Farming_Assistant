from getpass import getpass
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sqlalchemy import select
from app.database import Base, SessionLocal, engine
from app.models import User, Farmer
from app.services.farmer_service import create_farmer
from app.services.security_service import hash_password


def main():
    email = input("Admin email: ").strip().lower()
    password = getpass("Admin password (8+ chars): ")
    name = input("Admin display name: ").strip() or "Administrator"
    if len(password) < 8:
        raise SystemExit("Password must be at least 8 characters")
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        existing = db.scalar(select(User).where(User.email == email))
        if existing:
            existing.role = "admin"
            existing.is_active = True
            existing.token_version += 1
            db.commit()
            print("Existing account promoted to admin.")
            return
        farmer = create_farmer(db, full_name=name, language="en")
        user = User(email=email, farmer_id=farmer.id, password_hash=hash_password(password), role="admin")
        db.add(user)
        db.commit()
        print("Admin created:", email)


if __name__ == "__main__":
    main()
