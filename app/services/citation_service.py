from __future__ import annotations

from typing import Any


def _author_list(authors: list[str] | str | None) -> list[str]:
    if authors is None:
        return []
    if isinstance(authors, str):
        return [a.strip() for a in authors.split(",") if a.strip()]
    return [str(a).strip() for a in authors if str(a).strip()]


def _year(value: Any) -> str:
    if value is None:
        return "n.d."
    text = str(value)
    if len(text) >= 4 and text[:4].isdigit():
        return text[:4]
    return text or "n.d."


def _title(meta: dict) -> str:
    return meta.get("title") or "Untitled"


def _source_link(meta: dict) -> str:
    return meta.get("pdf_url") or meta.get("entry_url") or meta.get("source_url") or ""


def _institution(meta: dict) -> str:
    return meta.get("institution") or meta.get("publisher") or meta.get("source_system") or ""


def format_apa(meta: dict) -> str:
    authors = _author_list(meta.get("authors") or meta.get("author"))
    year = _year(meta.get("published") or meta.get("publication_year"))
    title = _title(meta)
    source = _institution(meta)
    url = _source_link(meta)

    author_text = ", ".join(authors) if authors else "Unknown author"
    parts = [f"{author_text} ({year}). {title}."]
    if source:
        parts.append(source + ".")
    if url:
        parts.append(url)
    return " ".join(parts).strip()


def format_mla(meta: dict) -> str:
    authors = _author_list(meta.get("authors") or meta.get("author"))
    year = _year(meta.get("published") or meta.get("publication_year"))
    title = _title(meta)
    source = _institution(meta)
    url = _source_link(meta)

    author_text = ", ".join(authors) if authors else "Unknown author"
    parts = [f"{author_text}. \"{title}.\""]
    if source:
        parts.append(source + ",")
    parts.append(year + ".")
    if url:
        parts.append(url)
    return " ".join(parts).strip()


def format_chicago(meta: dict) -> str:
    authors = _author_list(meta.get("authors") or meta.get("author"))
    year = _year(meta.get("published") or meta.get("publication_year"))
    title = _title(meta)
    source = _institution(meta)
    url = _source_link(meta)

    author_text = ", ".join(authors) if authors else "Unknown author"
    parts = [f"{author_text}. {year}. \"{title}.\""]
    if source:
        parts.append(source + ".")
    if url:
        parts.append(url)
    return " ".join(parts).strip()


def format_bibtex(meta: dict) -> str:
    title = _title(meta)
    authors = _author_list(meta.get("authors") or meta.get("author"))
    year = _year(meta.get("published") or meta.get("publication_year"))
    url = _source_link(meta)
    source = _institution(meta)
    key_seed = "".join(ch for ch in title.lower() if ch.isalnum())[:20] or "paper"

    author_text = " and ".join(authors) if authors else "Unknown author"

    fields = [
        f"  title = {{{title}}}",
        f"  author = {{{author_text}}}",
        f"  year = {{{year}}}",
    ]
    if source:
        fields.append(f"  publisher = {{{source}}}")
    if url:
        fields.append(f"  url = {{{url}}}")

    return "@article{" + key_seed + ",\n" + ",\n".join(fields) + "\n}"


def format_ris(meta: dict) -> str:
    title = _title(meta)
    authors = _author_list(meta.get("authors") or meta.get("author"))
    year = _year(meta.get("published") or meta.get("publication_year"))
    url = _source_link(meta)

    lines = ["TY  - JOUR"]
    for author in authors:
        lines.append(f"AU  - {author}")
    lines.append(f"TI  - {title}")
    lines.append(f"PY  - {year}")
    if url:
        lines.append(f"UR  - {url}")
    lines.append("ER  -")
    return "\n".join(lines)


def format_all_citations(meta: dict) -> dict:
    return {
        "apa": format_apa(meta),
        "mla": format_mla(meta),
        "chicago": format_chicago(meta),
        "bibtex": format_bibtex(meta),
        "ris": format_ris(meta),
    }
