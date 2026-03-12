from pathlib import Path
import sys
import pandas as pd
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from config.settings import RAW_DIR, PROCESSED_DIR
from app.services.document_parser import parse_document
from app.utils.chunking import chunk_text
from app.utils.text_cleaning import clean_text


DOCUMENT_DIR = RAW_DIR / "sample_research_documents"


def infer_title(text: str, fallback_name: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for line in lines[:5]:
        if line.lower().startswith("title:"):
            return line.replace("Title:", "").strip()
    return fallback_name


def infer_section(text: str) -> str:
    lower = text.lower()
    if "abstract" in lower:
        return "abstract_or_mixed"
    return "unknown"


def main():
    documents = []
    chunks = []

    files = sorted([
        p for p in DOCUMENT_DIR.iterdir()
        if p.is_file() and p.suffix.lower() in [".txt", ".pdf", ".docx"]
    ])

    for doc_idx, file_path in enumerate(files, start=1):
        parsed = parse_document(str(file_path))
        cleaned_text = clean_text(parsed["text"])
        title = infer_title(parsed["text"], file_path.stem)

        document_id = f"DOC_{doc_idx:04d}"
        doc_chunks = chunk_text(cleaned_text, chunk_size=1200, overlap=200)

        documents.append({
            "document_id": document_id,
            "file_name": parsed["file_name"],
            "file_type": parsed["file_type"],
            "title": title,
            "source_path": parsed["file_path"],
            "char_count": parsed["char_count"],
            "chunk_count": len(doc_chunks),
            "loaded_at": datetime.utcnow().isoformat(),
        })

        for chunk_idx, chunk in enumerate(doc_chunks, start=1):
            chunks.append({
                "document_id": document_id,
                "chunk_id": f"{document_id}_CHUNK_{chunk_idx:03d}",
                "chunk_order": chunk_idx,
                "section_guess": infer_section(chunk),
                "chunk_text": chunk,
                "chunk_char_count": len(chunk),
            })

    registry_df = pd.DataFrame(documents)
    chunks_df = pd.DataFrame(chunks)

    registry_path = PROCESSED_DIR / "document_registry.csv"
    chunks_path = PROCESSED_DIR / "document_chunks.csv"

    registry_df.to_csv(registry_path, index=False)
    chunks_df.to_csv(chunks_path, index=False)

    print("Document store build complete.\n")
    print("Saved outputs:")
    print("-", registry_path)
    print("-", chunks_path)

    print("\nDocument registry:")
    print(registry_df)

    print("\nDocument chunks preview:")
    print(chunks_df.head(10))


if __name__ == "__main__":
    main()
