from pathlib import Path
import requests
import xml.etree.ElementTree as ET
import fitz  # pymupdf

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DOC_DIR = PROJECT_ROOT / "data" / "raw" / "sample_research_documents"
TEMP_DIR = PROJECT_ROOT / "data" / "raw" / "temp_downloads"

ARXIV_API_URL = "http://export.arxiv.org/api/query"

RAW_DOC_DIR.mkdir(parents=True, exist_ok=True)
TEMP_DIR.mkdir(parents=True, exist_ok=True)
_SESSION = requests.Session()


def safe_text(value: str | None) -> str:
    if not value:
        return ""
    return " ".join(str(value).split())


def parse_arxiv_entry(entry) -> dict:
    ns = {
        "atom": "http://www.w3.org/2005/Atom",
        "arxiv": "http://arxiv.org/schemas/atom",
    }

    title = safe_text(entry.findtext("atom:title", default="", namespaces=ns))
    summary = safe_text(entry.findtext("atom:summary", default="", namespaces=ns))
    entry_id = safe_text(entry.findtext("atom:id", default="", namespaces=ns))
    published = safe_text(entry.findtext("atom:published", default="", namespaces=ns))
    updated = safe_text(entry.findtext("atom:updated", default="", namespaces=ns))

    authors = entry.findall("atom:author", ns)
    author_names = []
    for author in authors:
        name = safe_text(author.findtext("atom:name", default="", namespaces=ns))
        if name:
            author_names.append(name)

    pdf_url = ""
    for link in entry.findall("atom:link", ns):
        title_attr = link.attrib.get("title", "")
        href = link.attrib.get("href", "")
        if title_attr == "pdf" and href:
            pdf_url = href
            break

    primary_category = ""
    category = entry.find("arxiv:primary_category", ns)
    if category is not None:
        primary_category = category.attrib.get("term", "")

    categories = []
    for cat in entry.findall("atom:category", ns):
        term = cat.attrib.get("term", "")
        if term:
            categories.append(term)

    arxiv_id = entry_id.split("/")[-1] if entry_id else ""

    return {
        "arxiv_id": arxiv_id,
        "title": title,
        "summary": summary,
        "published": published,
        "updated": updated,
        "authors": author_names,
        "primary_category": primary_category,
        "categories": categories,
        "pdf_url": pdf_url,
        "entry_id": entry_id,
        "source_system": "arXiv",
    }


def search_arxiv(query: str, max_results: int = 10) -> list[dict]:
    params = {
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": max_results,
    }

    response = _SESSION.get(
        ARXIV_API_URL,
        params=params,
        timeout=60,
        headers={"User-Agent": "FrontierResearchIntelligence/1.0"},
    )
    response.raise_for_status()

    root = ET.fromstring(response.text)
    ns = {
        "atom": "http://www.w3.org/2005/Atom",
        "arxiv": "http://arxiv.org/schemas/atom",
    }

    entries = root.findall("atom:entry", ns)
    results = [parse_arxiv_entry(entry) for entry in entries]

    return results


def fetch_arxiv_by_id(arxiv_id: str) -> dict | None:
    params = {
        "search_query": f"id:{arxiv_id}",
        "start": 0,
        "max_results": 1,
    }

    response = _SESSION.get(
        ARXIV_API_URL,
        params=params,
        timeout=60,
        headers={"User-Agent": "FrontierResearchIntelligence/1.0"},
    )
    response.raise_for_status()

    root = ET.fromstring(response.text)
    ns = {
        "atom": "http://www.w3.org/2005/Atom",
        "arxiv": "http://arxiv.org/schemas/atom",
    }

    entry = root.find("atom:entry", ns)
    if entry is None:
        return None

    return parse_arxiv_entry(entry)


def slugify_filename(value: str) -> str:
    cleaned = "".join(ch if ch.isalnum() else "_" for ch in value.lower())
    while "__" in cleaned:
        cleaned = cleaned.replace("__", "_")
    return cleaned.strip("_")[:80]


def build_text_document_from_arxiv(record: dict) -> Path:
    title = record.get("title", "Untitled")
    authors = ", ".join(record.get("authors", [])) if record.get("authors") else "Unknown"
    topic = record.get("primary_category", "Unknown")
    arxiv_id = record.get("arxiv_id", "")
    published = record.get("published", "")
    updated = record.get("updated", "")
    pdf_url = record.get("pdf_url", "")
    entry_id = record.get("entry_id", "")
    categories = ", ".join(record.get("categories", []))
    citation = f"{authors} ({published[:4]}). {title}. arXiv:{arxiv_id}"

    content = f"""Title: {title}
Author: {authors}
Institution: arXiv Submission
Topic: {topic}
Citation: {citation}
Source System: arXiv
Source Paper ID: {arxiv_id}
Published: {published}
Updated: {updated}
PDF URL: {pdf_url}
Entry URL: {entry_id}
Categories: {categories}

Abstract:
{record.get("summary", "")}

Methods:
Not explicitly parsed yet. This document was auto-generated from arXiv metadata and abstract.

Results:
The full text has not yet been structurally parsed. This record currently reflects arXiv abstract-level ingestion.

Limitations:
This is an abstract-derived research document and may not contain full methods, results, or appendix material.

Conclusion:
This document was automatically ingested from arXiv and is now available for metadata search, summary display, and grounded Q&A.
"""

    file_name = f"arxiv_{slugify_filename(arxiv_id or title)}.txt"
    out_path = RAW_DOC_DIR / file_name
    out_path.write_text(content, encoding="utf-8")
    return out_path


def download_arxiv_pdf(record: dict) -> Path | None:
    pdf_url = record.get("pdf_url", "")
    arxiv_id = record.get("arxiv_id", "")

    if not pdf_url:
        return None

    out_path = TEMP_DIR / f"{slugify_filename(arxiv_id or 'paper')}.pdf"

    response = _SESSION.get(
        pdf_url,
        timeout=120,
        headers={"User-Agent": "FrontierResearchIntelligence/1.0"},
    )
    response.raise_for_status()

    out_path.write_bytes(response.content)
    return out_path


def extract_text_from_pdf(pdf_path: Path) -> str:
    text_parts = []
    with fitz.open(pdf_path) as doc:
        for page in doc:
            text_parts.append(page.get_text())
    return "\n".join(text_parts)


def build_fulltext_document_from_arxiv_pdf(record: dict) -> Path:
    title = record.get("title", "Untitled")
    authors = ", ".join(record.get("authors", [])) if record.get("authors") else "Unknown"
    topic = record.get("primary_category", "Unknown")
    arxiv_id = record.get("arxiv_id", "")
    published = record.get("published", "")
    updated = record.get("updated", "")
    pdf_url = record.get("pdf_url", "")
    entry_id = record.get("entry_id", "")
    categories = ", ".join(record.get("categories", []))
    citation = f"{authors} ({published[:4]}). {title}. arXiv:{arxiv_id}"

    pdf_path = download_arxiv_pdf(record)
    extracted_text = ""

    if pdf_path and pdf_path.exists():
        try:
            extracted_text = extract_text_from_pdf(pdf_path)
        except Exception as e:
            extracted_text = f"PDF extraction failed: {e}"

    if not extracted_text.strip():
        extracted_text = record.get("summary", "")

    content = f"""Title: {title}
Author: {authors}
Institution: arXiv Submission
Topic: {topic}
Citation: {citation}
Source System: arXiv
Source Paper ID: {arxiv_id}
Published: {published}
Updated: {updated}
PDF URL: {pdf_url}
Entry URL: {entry_id}
Categories: {categories}

Abstract:
{record.get("summary", "")}

Full Text:
{extracted_text}
"""

    file_name = f"arxiv_full_{slugify_filename(arxiv_id or title)}.txt"
    out_path = RAW_DOC_DIR / file_name
    out_path.write_text(content, encoding="utf-8", errors="ignore")
    return out_path
