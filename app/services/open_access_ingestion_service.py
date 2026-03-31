from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import mimetypes
import os
import re
from typing import Any, Dict, List
from urllib.parse import urljoin, urlparse, urlunparse

import requests
from bs4 import BeautifulSoup

from app.services.federated_search_service import SOURCE_TARGETS as FEDERATED_SOURCE_TARGETS, federated_search
from app.services.persistence_service import (
    get_featured_open_access_sources,
    log_open_access_ingestion_run,
    upsert_open_access_source,
    upsert_open_access_source_assets,
)
from app.services.source_connector_service import search_arxiv


USER_AGENT = "FrontierResearchIntelligence/1.0 (+ethical-open-access-ingestion)"
SESSION = requests.Session()
SESSION.headers.update({"User-Agent": USER_AGENT})

CURATED_ALLOWED_HOSTS = {
    "arxiv.org",
    "export.arxiv.org",
    "openalex.org",
    "api.openalex.org",
    "europepmc.org",
    "www.ebi.ac.uk",
    "doaj.org",
    "api.lib.harvard.edu",
    "dash.harvard.edu",
    "dspace.mit.edu",
    "mediatum.ub.tum.de",
    "ora.ox.ac.uk",
    "repository.cam.ac.uk",
}

CURATED_ALLOWED_SUFFIXES = (
    ".edu",
    ".ac.uk",
    ".ac.ca",
    ".edu.au",
    ".ac.jp",
    ".ac.kr",
    ".ac.in",
    ".ac.nz",
    ".ac.za",
    ".ac.ir",
    ".ac.id",
    ".ac.th",
    ".ac.il",
    ".edu.sg",
    ".edu.hk",
    ".edu.tw",
    ".edu.tr",
    ".edu.sa",
    ".edu.eg",
    ".edu.ar",
    ".edu.co",
    ".edu.pe",
    ".edu.cl",
    ".edu.ca",
    ".gc.ca",
    ".gob.mx",
    ".uni-heidelberg.de",
    ".uni-muenchen.de",
    ".univ-paris.fr",
    ".unibo.it",
    ".edu.br",
    ".edu.cn",
    ".edu.mx",
)

PUBLIC_ACCESS_HINTS = (
    "open access",
    "public repository",
    "institutional repository",
    "creative commons",
    "full text",
    "download pdf",
)

PAYWALL_HINTS = (
    "purchase pdf",
    "buy this article",
    "institutional login",
    "sign in to access",
    "subscribe to continue",
    "rent this article",
    "request access",
)


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _clean_text(value: Any) -> str:
    if value is None:
        return ""
    return " ".join(str(value).split()).strip()


def _clean_optional_text(value: Any) -> str | None:
    cleaned = _clean_text(value)
    return cleaned or None


def _normalize_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        items = value
    else:
        items = re.split(r"[;,|]", str(value))

    cleaned: List[str] = []
    for item in items:
        text = _clean_text(item)
        if text and text not in cleaned:
            cleaned.append(text[:250])
    return cleaned


def _normalize_language_code(value: Any) -> str:
    text = _clean_text(value).lower()
    if not text:
        return "und"
    if len(text) == 2:
        return text
    if "-" in text:
        return text.split("-", 1)[0]
    if "english" in text:
        return "en"
    if "spanish" in text:
        return "es"
    if "french" in text:
        return "fr"
    if "german" in text:
        return "de"
    if "portuguese" in text:
        return "pt"
    if "chinese" in text:
        return "zh"
    if "japanese" in text:
        return "ja"
    return text[:8] or "und"


def _canonicalize_url(value: str) -> str:
    parsed = urlparse(_clean_text(value))
    scheme = parsed.scheme.lower() or "https"
    netloc = parsed.netloc.lower()
    return urlunparse((scheme, netloc, parsed.path, parsed.params, parsed.query, ""))


def _host_for_url(value: str) -> str:
    return (urlparse(value).hostname or "").lower().strip(".")


def _allowed_hosts() -> set[str]:
    env_hosts = {
        _clean_text(item).lower()
        for item in os.getenv("OPEN_ACCESS_ALLOWED_HOSTS", "").split(",")
        if _clean_text(item)
    }
    return CURATED_ALLOWED_HOSTS | env_hosts


def _is_allowlisted_host(host: str) -> bool:
    host = (host or "").lower().strip(".")
    if not host:
        return False
    if host in _allowed_hosts():
        return True
    return any(host.endswith(suffix) for suffix in CURATED_ALLOWED_SUFFIXES)


def _is_allowlisted_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme in {"http", "https"} and _is_allowlisted_host(parsed.hostname or "")


def _guess_source_type(url: str, source_system: str) -> str:
    lowered = url.lower()
    if source_system == "arxiv":
        return "preprint"
    if lowered.endswith(".pdf"):
        return "repository_pdf"
    if "repository" in lowered or "handle.net" in lowered:
        return "repository_record"
    return "repository_page"


def _parse_publication_year(value: Any) -> int | None:
    text = _clean_text(value)
    if not text:
        return None
    match = re.search(r"(19|20)\d{2}", text)
    if not match:
        return None
    return int(match.group(0))


def _parse_published_at(value: Any) -> str | None:
    text = _clean_text(value)
    if not text:
        return None

    if re.fullmatch(r"\d{4}", text):
        return f"{text}-01-01T00:00:00+00:00"

    for raw in (text.replace("Z", "+00:00"), text):
        try:
            parsed = datetime.fromisoformat(raw)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc).isoformat()
        except ValueError:
            continue
    return None


def _build_source_key(source_system: str, source_paper_id: str | None, canonical_url: str) -> str:
    base = f"{source_system}|{source_paper_id or ''}|{canonical_url}"
    digest = hashlib.sha1(base.encode("utf-8")).hexdigest()[:24]
    return f"{source_system}:{digest}"


def _asset_type_for_url(asset_url: str, label: str) -> str:
    lowered = f"{asset_url} {label}".lower()
    if lowered.endswith(".pdf") or ".pdf" in lowered:
        return "pdf"
    if any(token in lowered for token in ("figure", "diagram", "chart", "graph", "plot")):
        return "diagram_image"
    return "image"


def _append_asset(assets: List[Dict[str, Any]], asset_url: str, label: str, is_primary: bool = False) -> None:
    canonical_url = _canonicalize_url(asset_url)
    if not _is_allowlisted_url(canonical_url):
        return
    if any(row["asset_url"] == canonical_url for row in assets):
        return

    mime_type = mimetypes.guess_type(canonical_url)[0]
    if not mime_type and canonical_url.lower().endswith(".pdf"):
        mime_type = "application/pdf"

    assets.append({
        "asset_type": _asset_type_for_url(canonical_url, label),
        "label": _clean_optional_text(label),
        "asset_url": canonical_url,
        "mime_type": mime_type,
        "is_primary": is_primary,
        "metadata": {
            "discovered_via": "page_parse",
        },
    })


def _normalize_record(raw: Dict[str, Any]) -> Dict[str, Any]:
    canonical_url = _canonicalize_url(raw.get("canonical_url") or raw.get("landing_page_url") or raw.get("pdf_url") or "")
    title = _clean_text(raw.get("title"))
    if not title or not canonical_url:
        raise ValueError("A verified open-access record requires both title and canonical_url.")
    if not _is_allowlisted_url(canonical_url):
        raise ValueError(f"URL host is not in the open-access allowlist: {canonical_url}")

    language_code = _normalize_language_code(raw.get("language_code"))
    abstract = _clean_optional_text(raw.get("abstract"))
    summary_seed_text = _clean_optional_text(raw.get("summary_seed_text") or abstract)
    audio_seed_text = _clean_optional_text(raw.get("audio_seed_text") or summary_seed_text)
    source_system = _clean_text(raw.get("source_system") or "open_access")
    source_paper_id = _clean_optional_text(raw.get("source_paper_id"))
    pdf_url = _clean_optional_text(raw.get("pdf_url"))
    if pdf_url:
        pdf_url = _canonicalize_url(pdf_url)
        if not _is_allowlisted_url(pdf_url):
            pdf_url = None

    readable_url = _clean_optional_text(raw.get("readable_url") or raw.get("landing_page_url") or canonical_url)
    if readable_url:
        readable_url = _canonicalize_url(readable_url)
        if not _is_allowlisted_url(readable_url):
            readable_url = canonical_url

    publication_year = _parse_publication_year(raw.get("publication_year") or raw.get("published_at"))
    normalized = {
        "source_key": _build_source_key(source_system, source_paper_id, canonical_url),
        "source_system": source_system,
        "source_type": _clean_text(raw.get("source_type") or _guess_source_type(canonical_url, source_system)),
        "ingestion_method": _clean_text(raw.get("ingestion_method") or "api"),
        "access_basis": _clean_text(raw.get("access_basis") or "open_access"),
        "verification_status": _clean_text(raw.get("verification_status") or "verified"),
        "verification_method": _clean_text(raw.get("verification_method") or "connector_policy"),
        "source_domain": _host_for_url(canonical_url),
        "source_paper_id": source_paper_id,
        "title": title[:500],
        "translated_title": _clean_optional_text(raw.get("translated_title")),
        "abstract": abstract,
        "summary_seed_text": summary_seed_text,
        "audio_seed_text": audio_seed_text,
        "language_code": language_code,
        "authors": _normalize_list(raw.get("authors")),
        "institutions": _normalize_list(raw.get("institutions")),
        "topics": _normalize_list(raw.get("topics")),
        "categories": _normalize_list(raw.get("categories")),
        "keywords": _normalize_list(raw.get("keywords")),
        "publication_year": publication_year,
        "published_at": _parse_published_at(raw.get("published_at")),
        "canonical_url": canonical_url,
        "landing_page_url": _clean_optional_text(raw.get("landing_page_url")) or canonical_url,
        "readable_url": readable_url,
        "pdf_url": pdf_url,
        "open_access_url": _clean_optional_text(raw.get("open_access_url")) or pdf_url or readable_url,
        "license_name": _clean_optional_text(raw.get("license_name")),
        "license_url": _clean_optional_text(raw.get("license_url")),
        "rights_statement": _clean_optional_text(raw.get("rights_statement")),
        "usage_constraints": _clean_optional_text(raw.get("usage_constraints"))
        or "Public/open-access source only. Verify downstream redistribution and translation rights per source before republishing full text or assets.",
        "provenance": raw.get("provenance") or {},
        "metadata": raw.get("metadata") or {},
        "is_featured": bool(raw.get("is_featured")),
        "is_multilingual": language_code not in {"und", "en"},
        "is_summary_ready": bool(summary_seed_text or pdf_url),
        "is_audio_ready": bool(audio_seed_text or summary_seed_text),
        "last_verified_at": _utcnow_iso(),
    }
    normalized["metadata"] = {
        **normalized["metadata"],
        "allowlisted_host": normalized["source_domain"],
        "user_agent": USER_AGENT,
    }
    return normalized


def _build_arxiv_record(row: Dict[str, Any]) -> Dict[str, Any]:
    entry_url = row.get("entry_id") or f"https://arxiv.org/abs/{row.get('arxiv_id', '')}"
    pdf_url = row.get("pdf_url")
    assets: List[Dict[str, Any]] = []
    if pdf_url:
        _append_asset(assets, pdf_url, "Primary PDF", is_primary=True)

    return {
        **_normalize_record({
            "source_system": "arxiv",
            "source_type": "preprint",
            "ingestion_method": "api",
            "access_basis": "open_repository",
            "verification_method": "official_api",
            "source_paper_id": row.get("arxiv_id"),
            "title": row.get("title"),
            "abstract": row.get("summary"),
            "summary_seed_text": row.get("summary"),
            "audio_seed_text": row.get("summary"),
            "language_code": "en",
            "authors": row.get("authors", []),
            "topics": [row.get("primary_category")] if row.get("primary_category") else [],
            "categories": row.get("categories", []),
            "publication_year": row.get("published"),
            "published_at": row.get("published"),
            "canonical_url": entry_url,
            "landing_page_url": entry_url,
            "readable_url": entry_url,
            "pdf_url": pdf_url,
            "open_access_url": pdf_url or entry_url,
            "license_name": "Repository open access",
            "usage_constraints": "Use metadata, abstracts, and source links responsibly. Verify any downstream redistribution rights for full-text reuse.",
            "provenance": {
                "connector_name": "arxiv_api",
                "verified_via": "official_api",
                "collection_policy": "api_first",
            },
            "metadata": {
                "updated": row.get("updated"),
                "entry_url": entry_url,
            },
        }),
        "assets": assets,
    }


def _build_federated_record(row: Dict[str, Any]) -> Dict[str, Any] | None:
    if row.get("connector_type") == "error":
        return None

    canonical_url = row.get("open_access_url") or row.get("source_url") or row.get("external_id")
    if not canonical_url:
        return None

    assets: List[Dict[str, Any]] = []
    if row.get("pdf_url"):
        _append_asset(assets, row["pdf_url"], "Source PDF", is_primary=True)

    source_system = _clean_text(row.get("source") or "federated")
    return {
        **_normalize_record({
            "source_system": source_system,
            "source_type": "repository_record",
            "ingestion_method": "api",
            "access_basis": "open_access_link",
            "verification_method": row.get("connector_type") or "institution_api",
            "source_paper_id": row.get("external_id"),
            "title": row.get("title"),
            "abstract": row.get("abstract"),
            "summary_seed_text": row.get("abstract"),
            "audio_seed_text": row.get("abstract"),
            "language_code": row.get("language_code") or "und",
            "authors": row.get("authors", []),
            "institutions": [row.get("institution")] if row.get("institution") else [],
            "topics": [row.get("topic")] if row.get("topic") else [],
            "categories": row.get("categories", []),
            "publication_year": row.get("published"),
            "published_at": row.get("published"),
            "canonical_url": canonical_url,
            "landing_page_url": row.get("source_url") or canonical_url,
            "readable_url": row.get("open_access_url") or row.get("source_url") or canonical_url,
            "pdf_url": row.get("pdf_url"),
            "open_access_url": row.get("open_access_url") or row.get("pdf_url") or canonical_url,
            "license_name": "Open/public source link",
            "usage_constraints": "Verify the linked repository terms for reuse beyond linking, summarization, and user-directed access.",
            "provenance": {
                "connector_name": source_system,
                "verified_via": row.get("connector_type") or "institution_api",
                "collection_policy": "api_first",
            },
            "metadata": {
                "availability": row.get("availability"),
            },
        }),
        "assets": assets,
    }


def _extract_meta_values(soup: BeautifulSoup, names: List[str]) -> List[str]:
    values: List[str] = []
    lowered = {name.lower() for name in names}
    for tag in soup.find_all("meta"):
        key = _clean_text(tag.get("name") or tag.get("property") or tag.get("http-equiv")).lower()
        if key in lowered:
            value = _clean_text(tag.get("content"))
            if value:
                values.append(value)
    return values


def _extract_text_snippet(soup: BeautifulSoup) -> str:
    body = soup.get_text(" ", strip=True)
    return _clean_text(body)[:1500]


def _validate_page_access(page_url: str, page_text: str) -> None:
    lowered = page_text.lower()
    if any(token in lowered for token in PAYWALL_HINTS) and not any(token in lowered for token in PUBLIC_ACCESS_HINTS):
        raise ValueError(f"Rejected non-open page: {page_url}")


def _extract_assets_from_soup(soup: BeautifulSoup, page_url: str) -> List[Dict[str, Any]]:
    assets: List[Dict[str, Any]] = []

    for pdf_url in _extract_meta_values(soup, ["citation_pdf_url", "pdf_url"]):
        _append_asset(assets, urljoin(page_url, pdf_url), "Primary PDF", is_primary=True)

    for image_url in _extract_meta_values(soup, ["og:image", "twitter:image"]):
        _append_asset(assets, urljoin(page_url, image_url), "Preview image")

    for anchor in soup.find_all("a", href=True):
        href = urljoin(page_url, anchor["href"])
        label = _clean_text(anchor.get_text(" ", strip=True)) or _clean_text(anchor.get("title"))
        lowered = f"{href} {label}".lower()
        if ".pdf" in lowered or any(token in lowered for token in ("figure", "diagram", "chart", "graph", "plot")):
            _append_asset(assets, href, label or "Related asset", is_primary=".pdf" in lowered)
        if len(assets) >= 10:
            break

    for image in soup.find_all("img", src=True):
        src = urljoin(page_url, image["src"])
        label = _clean_text(image.get("alt"))
        if any(token in label.lower() for token in ("figure", "diagram", "chart", "graph", "plot")):
            _append_asset(assets, src, label or "Diagram image")
        if len(assets) >= 10:
            break

    return assets


def ingest_allowlisted_open_access_url(url: str) -> Dict[str, Any]:
    canonical_url = _canonicalize_url(url)
    if not _is_allowlisted_url(canonical_url):
        raise ValueError("URL host is not allowlisted for ethical ingestion. Add it to OPEN_ACCESS_ALLOWED_HOSTS after review if needed.")

    response = SESSION.get(canonical_url, timeout=60)
    response.raise_for_status()
    content_type = _clean_text(response.headers.get("Content-Type")).lower()

    if "pdf" in content_type or canonical_url.lower().endswith(".pdf"):
        title = _clean_text(urlparse(canonical_url).path.rsplit("/", 1)[-1].replace("-", " ").replace("_", " "))
        record = _normalize_record({
            "source_system": _host_for_url(canonical_url),
            "source_type": "repository_pdf",
            "ingestion_method": "polite_single_fetch",
            "access_basis": "public_repository",
            "verification_method": "allowlisted_host",
            "title": title or "Open-access PDF",
            "summary_seed_text": None,
            "audio_seed_text": None,
            "language_code": "und",
            "canonical_url": canonical_url,
            "landing_page_url": canonical_url,
            "readable_url": canonical_url,
            "pdf_url": canonical_url,
            "open_access_url": canonical_url,
            "license_name": None,
            "usage_constraints": "Publicly reachable PDF on an allowlisted host. Verify specific reuse rights before redistribution or translation.",
            "provenance": {
                "connector_name": "allowlisted_single_url_fetch",
                "verified_via": "content_type_pdf",
                "collection_policy": "single_fetch_only",
            },
        })
        assets = []
        _append_asset(assets, canonical_url, "Primary PDF", is_primary=True)
        return {"record": record, "assets": assets}

    soup = BeautifulSoup(response.text, "html.parser")
    page_text = _extract_text_snippet(soup)
    _validate_page_access(canonical_url, page_text)

    title_candidates = _extract_meta_values(soup, ["citation_title", "og:title"])
    description_candidates = _extract_meta_values(
        soup,
        ["citation_abstract", "description", "og:description", "dc.description", "dcterms.abstract"],
    )
    authors = _extract_meta_values(soup, ["citation_author", "dc.creator", "dcterms.creator"])
    keywords = _extract_meta_values(soup, ["citation_keywords", "keywords"])
    language_values = _extract_meta_values(soup, ["citation_language", "dc.language"])
    rights_values = _extract_meta_values(soup, ["dc.rights", "dcterms.rights", "citation_license"])
    license_urls = _extract_meta_values(soup, ["citation_license_url"])
    published_values = _extract_meta_values(soup, ["citation_publication_date", "dc.date", "dcterms.issued"])

    html_lang = _clean_text(soup.html.get("lang")) if soup.html else ""
    assets = _extract_assets_from_soup(soup, canonical_url)
    primary_pdf = next((asset["asset_url"] for asset in assets if asset["asset_type"] == "pdf"), None)

    record = _normalize_record({
        "source_system": _host_for_url(canonical_url),
        "source_type": _guess_source_type(canonical_url, _host_for_url(canonical_url)),
        "ingestion_method": "polite_single_fetch",
        "access_basis": "public_repository",
        "verification_method": "allowlisted_host",
        "title": title_candidates[0] if title_candidates else soup.title.string if soup.title and soup.title.string else "Open-access page",
        "abstract": description_candidates[0] if description_candidates else None,
        "summary_seed_text": description_candidates[0] if description_candidates else page_text,
        "audio_seed_text": description_candidates[0] if description_candidates else page_text,
        "language_code": language_values[0] if language_values else html_lang,
        "authors": authors,
        "keywords": keywords,
        "publication_year": published_values[0] if published_values else None,
        "published_at": published_values[0] if published_values else None,
        "canonical_url": canonical_url,
        "landing_page_url": canonical_url,
        "readable_url": canonical_url,
        "pdf_url": primary_pdf,
        "open_access_url": primary_pdf or canonical_url,
        "license_name": rights_values[0] if rights_values else None,
        "license_url": license_urls[0] if license_urls else None,
        "rights_statement": rights_values[0] if rights_values else None,
        "usage_constraints": "Only ingest allowlisted public repository pages. No recursive crawling, no paywalled content, and verify asset rights before reuse.",
        "provenance": {
            "connector_name": "allowlisted_single_url_fetch",
            "verified_via": "allowlisted_host_and_page_parse",
            "collection_policy": "single_fetch_only",
        },
        "metadata": {
            "content_type": content_type,
        },
    })

    return {"record": record, "assets": assets}


def _dedupe_records(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    deduped: List[Dict[str, Any]] = []
    seen: set[str] = set()
    for row in records:
        key = row.get("source_key") or row.get("canonical_url")
        if not key or key in seen:
            continue
        seen.add(key)
        deduped.append(row)
    return deduped


VALID_OPEN_ACCESS_SOURCE_TARGETS = ("arxiv",) + FEDERATED_SOURCE_TARGETS


def search_verified_open_access_records(
    query: str,
    limit_per_source: int = 25,
    page: int = 1,
    source_targets: tuple[str, ...] | None = None,
) -> List[Dict[str, Any]]:
    query = _clean_text(query)
    if not query:
        return []

    results: List[Dict[str, Any]] = []
    targets = set(source_targets or VALID_OPEN_ACCESS_SOURCE_TARGETS)

    if "arxiv" in targets:
        for row in search_arxiv(query, max_results=max(1, min(limit_per_source, 100))):
            results.append(_build_arxiv_record(row))

    federated_targets = tuple(target for target in targets if target in FEDERATED_SOURCE_TARGETS)
    for row in federated_search(
        query,
        limit_per_source=max(1, min(limit_per_source, 100)),
        page=max(1, page),
        source_targets=federated_targets or None,
    ):
        normalized = _build_federated_record(row)
        if normalized:
            results.append(normalized)

    return _dedupe_records(results)


def persist_verified_open_access_url(
    url: str,
    requested_by_clerk_user_id: str | None = None,
    mark_featured: bool = False,
) -> Dict[str, Any]:
    canonical_url = _canonicalize_url(url)
    source_domain = _host_for_url(canonical_url)

    try:
        parsed = ingest_allowlisted_open_access_url(canonical_url)
        row = parsed["record"].copy()
        row["is_featured"] = bool(mark_featured)

        source = upsert_open_access_source(row)
        assets = upsert_open_access_source_assets(source["id"], parsed.get("assets", []))
        run = log_open_access_ingestion_run({
            "requested_by_clerk_user_id": requested_by_clerk_user_id,
            "connector_name": "allowlisted_single_url_fetch",
            "requested_url": canonical_url,
            "source_domain": source_domain,
            "source_type": row.get("source_type"),
            "ingestion_method": row.get("ingestion_method"),
            "status": "completed",
            "record_count": 1,
            "warning_count": 0,
            "warnings": [],
            "metadata": {
                "source_key": source.get("source_key"),
                "featured": bool(mark_featured),
            },
            "completed_at": _utcnow_iso(),
        })
        return {
            "success": True,
            "source": source,
            "assets": assets,
            "ingestion_run": run,
        }
    except Exception as exc:
        run = log_open_access_ingestion_run({
            "requested_by_clerk_user_id": requested_by_clerk_user_id,
            "connector_name": "allowlisted_single_url_fetch",
            "requested_url": canonical_url,
            "source_domain": source_domain,
            "source_type": _guess_source_type(canonical_url, source_domain),
            "ingestion_method": "polite_single_fetch",
            "status": "failed",
            "record_count": 0,
            "warning_count": 1,
            "warnings": [_clean_text(exc)],
            "metadata": {
                "failure_stage": "ingest",
            },
            "completed_at": _utcnow_iso(),
        })
        return {
            "success": False,
            "message": _clean_text(exc),
            "ingestion_run": run,
        }


def get_featured_verified_open_access_sources(limit: int = 12) -> List[Dict[str, Any]]:
    try:
        return get_featured_open_access_sources(limit=limit)
    except Exception:
        return []
