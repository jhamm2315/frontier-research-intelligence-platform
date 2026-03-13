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


def extract_field(text: str, field_name: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    prefix = f"{field_name}:"
    for line in lines[:20]:
        if line.lower().startswith(prefix.lower()):
            return line.replace(prefix, "").strip()
    return ""


def infer_title(text: str, fallback_name: str) -> str:
    return extract_field(text, "Title") or fallback_name


def infer_author(text: str) -> str:
    return extract_field(text, "Author") or "Unknown"


def infer_institution(text: str) -> str:
    return extract_field(text, "Institution") or "Unknown"


def infer_topic(text: str) -> str:
    return extract_field(text, "Topic") or "Unknown"


def infer_citation(text: str) -> str:
    return extract_field(text, "Citation") or ""


def infer_source_system(text: str) -> str:
    return extract_field(text, "Source System") or "Local"


def infer_source_paper_id(text: str) -> str:
    return extract_field(text, "Source Paper ID") or ""


def infer_published(text: str) -> str:
    return extract_field(text, "Published") or ""


def infer_updated(text: str) -> str:
    return extract_field(text, "Updated") or ""


def infer_pdf_url(text: str) -> str:
    return extract_field(text, "PDF URL") or ""


def infer_entry_url(text: str) -> str:
    return extract_field(text, "Entry URL") or ""


def infer_categories(text: str) -> str:
    return extract_field(text, "Categories") or ""


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
        author = infer_author(parsed["text"])
        institution = infer_institution(parsed["text"])
        topic = infer_topic(parsed["text"])
        citation = infer_citation(parsed["text"])

        source_system = infer_source_system(parsed["text"])
        source_paper_id = infer_source_paper_id(parsed["text"])
        published = infer_published(parsed["text"])
        updated = infer_updated(parsed["text"])
        pdf_url = infer_pdf_url(parsed["text"])
        entry_url = infer_entry_url(parsed["text"])
        categories = infer_categories(parsed["text"])

        document_id = f"DOC_{doc_idx:04d}"
        doc_chunks = chunk_text(cleaned_text, chunk_size=1200, overlap=200)

        documents.append({
            "document_id": document_id,
            "file_name": parsed["file_name"],
            "file_type": parsed["file_type"],
            "title": title,
            "author": author,
            "institution": institution,
            "topic": topic,
            "citation": citation,
            "source_system": source_system,
            "source_paper_id": source_paper_id,
            "published": published,
            "updated": updated,
            "pdf_url": pdf_url,
            "entry_url": entry_url,
            "categories": categories,
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

    registry_df.to_csv(PROCESSED_DIR / "document_registry.csv", index=False)
    chunks_df.to_csv(PROCESSED_DIR / "document_chunks.csv", index=False)

    print("Document store build complete.")
    print(registry_df.tail(10))


if __name__ == "__main__":
    main()
