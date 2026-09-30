from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.services.rag_service import ingest_directory

if __name__ == "__main__":
    count = ingest_directory(ROOT / "data" / "knowledge")
    print(f"Indexed {count} chunks.")
