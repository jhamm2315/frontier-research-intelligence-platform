from pathlib import Path
import shutil
import pandas as pd
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DOC_DIR = PROJECT_ROOT / "data" / "raw" / "sample_research_documents"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"


def normalize_title(value: str) -> str:
    if pd.isna(value):
        return ""
    return " ".join(str(value).lower().split())


def get_next_document_id(registry: pd.DataFrame) -> str:
    if registry.empty:
        return "DOC_0001"

    existing = (
        registry["document_id"]
        .astype(str)
        .str.replace("DOC_", "", regex=False)
    )

    nums = pd.to_numeric(existing, errors="coerce").dropna()
    next_num = int(nums.max()) + 1 if not nums.empty else 1
    return f"DOC_{next_num:04d}"


def ingest_existing_file(file_path: str, title: str, author: str = "Unknown",
                         institution: str = "Unknown", topic: str = "Unknown",
                         citation: str = "") -> dict:
    source = Path(file_path)

    if not source.exists():
        return {"success": False, "message": f"Source file not found: {file_path}"}

    registry_path = PROCESSED_DIR / "document_registry.csv"
    if registry_path.exists():
        registry = pd.read_csv(registry_path)
    else:
        registry = pd.DataFrame()

    document_id = get_next_document_id(registry)
    dest_name = f"{document_id}_{source.name}"
    dest_path = RAW_DOC_DIR / dest_name

    shutil.copy2(source, dest_path)

    return {
        "success": True,
        "document_id": document_id,
        "stored_path": str(dest_path),
        "title": title,
        "author": author,
        "institution": institution,
        "topic": topic,
        "citation": citation,
        "message": "File copied into raw document store. Rebuild document store next."
    }
