from typing import Dict, Any
from datetime import datetime

# In-memory store (replace later with DB)
UPLOADED_DOCS: Dict[str, Dict[str, Any]] = {}


def register_uploaded_doc(doc: Dict[str, Any]) -> str:
    doc_id = f"uploaded_{len(UPLOADED_DOCS) + 1}"

    UPLOADED_DOCS[doc_id] = {
        "document_id": doc_id,
        "title": doc.get("file_name", "Uploaded Document"),
        "author": "User Upload",
        "institution": "Local Upload",
        "topic": "User Provided",
        "source_system": "uploaded",
        "publication_year": datetime.utcnow().year,
        "pdf_url": None,
        "content": doc.get("text", ""),
        "summary": doc.get("summary", ""),
        "created_at": datetime.utcnow().isoformat(),
    }

    return doc_id


def get_uploaded_doc(doc_id: str):
    return UPLOADED_DOCS.get(doc_id)


def list_uploaded_docs():
    return list(UPLOADED_DOCS.values())
