from pathlib import Path
import fitz  # pymupdf
from docx import Document


def parse_txt(file_path: Path) -> str:
    return file_path.read_text(encoding="utf-8", errors="ignore")


def parse_pdf(file_path: Path) -> str:
    text_parts = []
    with fitz.open(file_path) as doc:
        for page in doc:
            text_parts.append(page.get_text())
    return "\n".join(text_parts)


def parse_docx(file_path: Path) -> str:
    doc = Document(str(file_path))
    return "\n".join([p.text for p in doc.paragraphs])


def parse_document(file_path: str) -> dict:
    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix == ".txt":
        text = parse_txt(path)
    elif suffix == ".pdf":
        text = parse_pdf(path)
    elif suffix == ".docx":
        text = parse_docx(path)
    else:
        raise ValueError(f"Unsupported document type: {suffix}")

    return {
        "file_path": str(path),
        "file_name": path.name,
        "file_type": suffix,
        "text": text,
        "char_count": len(text),
    }
