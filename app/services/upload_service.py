from __future__ import annotations

from pathlib import Path
from datetime import datetime
import shutil
import mimetypes
import requests

import fitz
from docx import Document
from bs4 import BeautifulSoup

PROJECT_ROOT = Path(__file__).resolve().parents[2]
UPLOAD_DIR = PROJECT_ROOT / "data" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def _timestamp() -> str:
    return datetime.utcnow().strftime("%Y%m%d_%H%M%S")


def save_uploaded_file(file_path: str) -> dict:
    source = Path(file_path)
    if not source.exists():
        raise FileNotFoundError(f"Upload source file not found: {file_path}")

    target = UPLOAD_DIR / f"{_timestamp()}_{source.name}"
    shutil.copy2(source, target)

    return {
        "file_name": target.name,
        "file_path": str(target),
        "mime_type": mimetypes.guess_type(str(target))[0],
        "extension": target.suffix.lower(),
        "saved_at": datetime.utcnow().isoformat(),
    }


def extract_text_from_txt(file_path: str) -> str:
    return Path(file_path).read_text(encoding="utf-8", errors="ignore")


def extract_text_from_pdf(file_path: str) -> str:
    text_parts = []
    with fitz.open(file_path) as doc:
        for page in doc:
            text_parts.append(page.get_text())
    return "\n".join(text_parts)


def extract_text_from_docx(file_path: str) -> str:
    doc = Document(file_path)
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())


def extract_text_from_file(file_path: str) -> dict:
    path = Path(file_path)
    ext = path.suffix.lower()

    if ext == ".txt":
        text = extract_text_from_txt(file_path)
    elif ext == ".pdf":
        text = extract_text_from_pdf(file_path)
    elif ext == ".docx":
        text = extract_text_from_docx(file_path)
    else:
        raise ValueError(f"Unsupported file type: {ext}")

    return {
        "file_name": path.name,
        "file_path": str(path),
        "extension": ext,
        "text": text,
        "char_count": len(text),
    }


def ingest_local_file(file_path: str) -> dict:
    saved = save_uploaded_file(file_path)
    extracted = extract_text_from_file(saved["file_path"])
    return {
        **saved,
        **extracted,
    }


def ingest_url(url: str) -> dict:
    response = requests.get(url, timeout=60, headers={"User-Agent": "FrontierResearchIntelligence/1.0"})
    response.raise_for_status()

    content_type = response.headers.get("Content-Type", "")
    html = response.text

    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.string.strip() if soup.title and soup.title.string else "Untitled URL Document"

    text = " ".join(t.strip() for t in soup.stripped_strings)
    file_name = f"{_timestamp()}_url_capture.txt"
    out_path = UPLOAD_DIR / file_name

    out_path.write_text(
        f"Title: {title}\nSource URL: {url}\n\n{text}",
        encoding="utf-8",
        errors="ignore"
    )

    return {
        "file_name": file_name,
        "file_path": str(out_path),
        "extension": ".txt",
        "source_url": url,
        "mime_type": content_type,
        "text": text,
        "char_count": len(text),
        "saved_at": datetime.utcnow().isoformat(),
    }
