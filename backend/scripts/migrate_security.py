from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sqlalchemy import inspect, text
from app.database import Base, engine
import app.models  # noqa: F401


def add_column_if_missing(conn, table: str, column: str, definition: str):
    inspector = inspect(conn)
    names = {item["name"] for item in inspector.get_columns(table)}
    if column not in names:
        conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {definition}"))
        print(f"Added {table}.{column}")


def main():
    with engine.begin() as conn:
        Base.metadata.create_all(bind=engine)
        add_column_if_missing(conn, "farmers", "land_size_acres", "DOUBLE NULL")
        add_column_if_missing(conn, "farmers", "irrigation_type", "VARCHAR(80) NOT NULL DEFAULT ''")
        add_column_if_missing(conn, "farmers", "soil_type", "VARCHAR(80) NOT NULL DEFAULT ''")
        add_column_if_missing(conn, "farmers", "farming_type", "VARCHAR(80) NOT NULL DEFAULT ''")
        add_column_if_missing(conn, "users", "farmer_id", "VARCHAR(36) NULL")
        add_column_if_missing(conn, "conversations", "farmer_id", "VARCHAR(36) NULL")
        try:
            conn.execute(text("CREATE INDEX idx_conversations_farmer_id ON conversations (farmer_id)"))
        except Exception:
            pass
    print("Security migration completed. Existing anonymous conversations may have farmer_id=NULL; new authenticated conversations are always owned.")


if __name__ == "__main__":
    main()
