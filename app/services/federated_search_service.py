from __future__ import annotations

import os
from typing import Any

import requests
from dotenv import load_dotenv


load_dotenv(dotenv_path=".env")

OPENALEX_BASE = "https://api.openalex.org"
HARVARD_LIBRARYCLOUD_BASE = "https://api.lib.harvard.edu/v2/items.json"
EUROPE_PMC_BASE = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
DOAJ_BASE = "https://doaj.org/api/search/articles"
OPENALEX_API_KEY = os.getenv("OPENALEX_API_KEY", "")

REQUEST_HEADERS = {
    "User-Agent": "FrontierResearchIntelligence/1.0 (+open-access-federated-search)",
}

GLOBAL_OPENALEX_INSTITUTIONS = (
    "Harvard University",
    "Massachusetts Institute of Technology",
    "Stanford University",
    "University of Oxford",
    "University of Cambridge",
    "ETH Zurich",
    "Technical University of Munich",
    "University of Toronto",
    "National University of Singapore",
    "University of Tokyo",
    "Sorbonne Universite",
    "University of Melbourne",
)

SOURCE_TARGETS = (
    "openalex_global",
    "openalex_institutions",
    "europe_pmc",
    "doaj",
    "harvard_librarycloud",
)


def _safe_get(d: Any, path: list[str], default=None):
    cur = d
    for key in path:
        if isinstance(cur, dict):
            cur = cur.get(key)
        else:
            return default
        if cur is None:
            return default
    return cur


def _ensure_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _request_json(url: str, params: dict[str, Any]) -> dict[str, Any]:
    response = requests.get(
        url,
        params=params,
        headers=REQUEST_HEADERS,
        timeout=60,
    )
    response.raise_for_status()
    return response.json()


def _reconstruct_openalex_abstract(inv_idx: dict | None) -> str:
    if not inv_idx or not isinstance(inv_idx, dict):
        return ""
    pos_to_word = {}
    for word, positions in inv_idx.items():
        for pos in positions:
            pos_to_word[pos] = word
    return " ".join(pos_to_word[pos] for pos in sorted(pos_to_word.keys()))


def _openalex_params(extra: dict | None = None) -> dict:
    params = extra.copy() if extra else {}
    if OPENALEX_API_KEY:
        params["api_key"] = OPENALEX_API_KEY
    return params


def _clean_author_string(value: str) -> list[str]:
    if not value:
        return []
    return [part.strip() for part in value.split(",") if part.strip()]


def _normalize_openalex_work(item: dict[str, Any], source: str, connector_type: str, institution_name: str | None = None) -> dict[str, Any]:
    title = item.get("title") or item.get("display_name") or "Untitled"
    abstract = _reconstruct_openalex_abstract(item.get("abstract_inverted_index"))
    authors = []
    institutions = []
    for authorship in item.get("authorships", []):
        author_name = _safe_get(authorship, ["author", "display_name"], "")
        if author_name:
            authors.append(author_name)
        for institution in authorship.get("institutions", []):
            inst_name = institution.get("display_name")
            if inst_name and inst_name not in institutions:
                institutions.append(inst_name)

    primary_location = item.get("primary_location") or {}
    location_source = primary_location.get("source") or {}
    oa_url = _safe_get(item, ["open_access", "oa_url"], "") or primary_location.get("landing_page_url") or primary_location.get("pdf_url")
    source_url = item.get("id", "")
    topics = [
        topic.get("display_name")
        for topic in item.get("topics", [])
        if topic.get("display_name")
    ]
    keywords = [
        keyword.get("display_name")
        for keyword in item.get("keywords", [])
        if keyword.get("display_name")
    ]

    return {
        "source": source,
        "connector_type": connector_type,
        "title": title,
        "authors": authors,
        "institution": institution_name or ", ".join(institutions[:2]) or location_source.get("display_name", ""),
        "institutions": institutions,
        "published": item.get("publication_date") or item.get("publication_year"),
        "abstract": abstract,
        "topic": topics[0] if topics else "",
        "topics": topics,
        "categories": [concept.get("display_name") for concept in item.get("concepts", []) if concept.get("display_name")][:8],
        "keywords": keywords[:12],
        "external_id": source_url,
        "source_url": source_url,
        "pdf_url": primary_location.get("pdf_url") or oa_url,
        "open_access_url": oa_url,
        "entry_url": primary_location.get("landing_page_url") or source_url,
        "availability": "open_access",
        "language_code": (item.get("language") or "und").lower(),
        "license": _safe_get(item, ["primary_location", "license"]),
        "result_count_hint": _safe_get(item, ["counts_by_year", 0, "works_count"]),
    }


def _find_institution_id(display_name: str) -> str | None:
    params = _openalex_params({
        "search": display_name,
        "per-page": 5,
    })
    data = _request_json(f"{OPENALEX_BASE}/institutions", params=params)
    results = data.get("results", [])
    for row in results:
        name = (row.get("display_name") or "").lower()
        if display_name.lower() in name or name in display_name.lower():
            return row.get("id", "").replace("https://openalex.org/", "")
    if results:
        return results[0].get("id", "").replace("https://openalex.org/", "")
    return None


def search_openalex_for_institution(query: str, institution_name: str, limit: int = 10, page: int = 1) -> list[dict]:
    institution_id = _find_institution_id(institution_name)
    if not institution_id:
        return []

    params = _openalex_params({
        "search": query,
        "filter": f"institutions.id:{institution_id},is_oa:true",
        "per-page": max(1, min(limit, 200)),
        "page": max(1, page),
        "sort": "relevance_score:desc",
    })
    data = _request_json(f"{OPENALEX_BASE}/works", params=params)
    return [
        _normalize_openalex_work(item, f"openalex_{institution_name.lower().replace(' ', '_')}", "institution_metadata", institution_name)
        for item in data.get("results", [])
    ]


def search_openalex_global_open_access(query: str, limit: int = 50, page: int = 1) -> list[dict]:
    params = _openalex_params({
        "search": query,
        "filter": "is_oa:true,has_fulltext:true",
        "per-page": max(1, min(limit, 200)),
        "page": max(1, page),
        "sort": "relevance_score:desc",
    })
    data = _request_json(f"{OPENALEX_BASE}/works", params=params)
    return [
        _normalize_openalex_work(item, "openalex_global", "global_open_access")
        for item in data.get("results", [])
    ]


def search_harvard_librarycloud(query: str, limit: int = 10, page: int = 1) -> list[dict]:
    params = {
        "q": query,
        "limit": max(1, min(limit, 100)),
        "start": max(0, (page - 1) * limit),
    }
    payload = _request_json(HARVARD_LIBRARYCLOUD_BASE, params=params)
    items = payload.get("items", {}).get("mods", [])
    items = _ensure_list(items)

    rows = []
    for item in items:
        if not isinstance(item, dict):
            continue

        title_info = item.get("titleInfo")
        if isinstance(title_info, list):
            title_info = title_info[0] if title_info else {}
        title = title_info.get("title", "Untitled") if isinstance(title_info, dict) else "Untitled"

        names = []
        for n in _ensure_list(item.get("name")):
            if isinstance(n, dict):
                name_part = n.get("namePart")
                if isinstance(name_part, list):
                    name_part = name_part[0] if name_part else ""
                if isinstance(name_part, dict):
                    value = name_part.get("_") or name_part.get("value") or ""
                else:
                    value = name_part or ""
                if value:
                    names.append(str(value))

        origin = item.get("originInfo")
        if isinstance(origin, list):
            origin = origin[0] if origin else {}
        published = ""
        if isinstance(origin, dict):
            issued = origin.get("dateIssued")
            if isinstance(issued, list):
                issued = issued[0] if issued else ""
            if isinstance(issued, dict):
                published = issued.get("_") or issued.get("value") or ""
            else:
                published = issued or ""

        abstract = item.get("abstract", "")
        if isinstance(abstract, list):
            abstract = abstract[0] if abstract else ""
        if isinstance(abstract, dict):
            abstract = abstract.get("_") or abstract.get("value") or ""

        source_url = ""
        for loc in _ensure_list(item.get("location")):
            if isinstance(loc, dict):
                url = loc.get("url")
                if isinstance(url, list):
                    url = url[0] if url else ""
                if isinstance(url, dict):
                    url = url.get("_") or url.get("value") or ""
                if url:
                    source_url = url
                    break

        rows.append({
            "source": "harvard_librarycloud",
            "connector_type": "institution_metadata",
            "title": title,
            "authors": names,
            "institution": "Harvard University",
            "institutions": ["Harvard University"],
            "published": published,
            "abstract": abstract or "",
            "topic": "",
            "topics": [],
            "categories": [],
            "keywords": [],
            "external_id": source_url,
            "source_url": source_url,
            "pdf_url": source_url if str(source_url).lower().endswith(".pdf") else "",
            "open_access_url": source_url,
            "entry_url": source_url,
            "availability": "metadata_or_link",
            "language_code": "und",
        })
    return rows


def search_europe_pmc(query: str, limit: int = 50, page: int = 1) -> list[dict]:
    params = {
        "query": f"({query}) AND OPEN_ACCESS:y",
        "format": "json",
        "pageSize": max(1, min(limit, 1000)),
        "page": max(1, page),
        "sort": "RELEVANCE",
    }
    payload = _request_json(EUROPE_PMC_BASE, params=params)
    rows = []
    for item in _safe_get(payload, ["resultList", "result"], []) or []:
        if not isinstance(item, dict):
            continue
        pmcid = item.get("pmcid")
        source_url = f"https://europepmc.org/article/MED/{item.get('pmid')}" if item.get("pmid") else ""
        if pmcid:
            source_url = f"https://europepmc.org/article/PMC/{pmcid}"
        pdf_url = f"https://europepmc.org/articles/{pmcid}?pdf=render" if pmcid else ""
        rows.append({
            "source": "europe_pmc",
            "connector_type": "open_access_biomedical",
            "title": item.get("title") or "Untitled",
            "authors": _clean_author_string(item.get("authorString", "")),
            "institution": item.get("journalTitle") or "Europe PMC",
            "institutions": [item.get("journalTitle")] if item.get("journalTitle") else [],
            "published": item.get("firstPublicationDate") or item.get("pubYear"),
            "abstract": item.get("abstractText") or "",
            "topic": item.get("keywordList", {}).get("keyword", [""])[0] if isinstance(item.get("keywordList"), dict) and item.get("keywordList", {}).get("keyword") else "",
            "topics": _ensure_list(_safe_get(item, ["keywordList", "keyword"], [])),
            "categories": [item.get("journalTitle")] if item.get("journalTitle") else [],
            "keywords": _ensure_list(_safe_get(item, ["keywordList", "keyword"], []))[:12],
            "external_id": pmcid or item.get("doi") or item.get("id"),
            "source_url": source_url,
            "pdf_url": pdf_url,
            "open_access_url": pdf_url or source_url,
            "entry_url": source_url,
            "availability": "open_access",
            "language_code": "en",
        })
    return rows


def search_doaj_articles(query: str, limit: int = 50, page: int = 1) -> list[dict]:
    params = {
        "page": max(1, page),
        "pageSize": max(1, min(limit, 100)),
    }
    payload = _request_json(f"{DOAJ_BASE}/{query}", params=params)
    rows = []
    for item in payload.get("results", []) or []:
        bibjson = item.get("bibjson", {})
        links = bibjson.get("link", []) or []
        fulltext_url = ""
        landing_url = ""
        for link in links:
            if not isinstance(link, dict):
                continue
            url = link.get("url") or ""
            link_type = (link.get("type") or "").lower()
            if not landing_url and url:
                landing_url = url
            if "fulltext" in link_type or str(url).lower().endswith(".pdf"):
                fulltext_url = url
                break
        authors = []
        for author in bibjson.get("author", []) or []:
            name = author.get("name")
            if name:
                authors.append(name)
        keywords = bibjson.get("keywords", []) or []
        journal = _safe_get(bibjson, ["journal", "title"], "")
        rows.append({
            "source": "doaj",
            "connector_type": "open_access_journal_directory",
            "title": bibjson.get("title") or "Untitled",
            "authors": authors,
            "institution": journal or "DOAJ",
            "institutions": [journal] if journal else [],
            "published": bibjson.get("year") or "",
            "abstract": bibjson.get("abstract") or "",
            "topic": keywords[0] if keywords else "",
            "topics": keywords[:8],
            "categories": keywords[:8],
            "keywords": keywords[:12],
            "external_id": item.get("id"),
            "source_url": landing_url,
            "pdf_url": fulltext_url if str(fulltext_url).lower().endswith(".pdf") else "",
            "open_access_url": fulltext_url or landing_url,
            "entry_url": landing_url,
            "availability": "open_access",
            "language_code": (bibjson.get("language", ["und"])[0] if isinstance(bibjson.get("language"), list) else bibjson.get("language") or "und").lower(),
            "license": _safe_get(bibjson, ["license", 0, "type"], ""),
        })
    return rows


def _error_row(source: str, institution: str, error: Exception) -> dict[str, Any]:
    return {
        "source": source,
        "connector_type": "error",
        "title": f"Connector error: {error}",
        "authors": [],
        "institution": institution,
        "institutions": [institution] if institution else [],
        "published": "",
        "abstract": "",
        "topic": "",
        "topics": [],
        "categories": [],
        "keywords": [],
        "external_id": "",
        "source_url": "",
        "pdf_url": "",
        "open_access_url": "",
        "entry_url": "",
        "availability": "error",
        "language_code": "und",
    }


def federated_search(
    query: str,
    limit_per_source: int = 25,
    page: int = 1,
    source_targets: tuple[str, ...] | None = None,
) -> list[dict]:
    results = []
    per_source = max(1, min(limit_per_source, 100))
    page = max(1, page)
    targets = set(source_targets or SOURCE_TARGETS)

    if "openalex_global" in targets:
        try:
            results.extend(search_openalex_global_open_access(query, limit=per_source, page=page))
        except Exception as exc:
            results.append(_error_row("openalex_global", "Global open access", exc))

    if "openalex_institutions" in targets:
        for institution_name in GLOBAL_OPENALEX_INSTITUTIONS:
            try:
                results.extend(search_openalex_for_institution(query, institution_name, limit=min(per_source, 25), page=page))
            except Exception as exc:
                results.append(_error_row(f"openalex_{institution_name.lower().replace(' ', '_')}", institution_name, exc))

    if "harvard_librarycloud" in targets:
        try:
            results.extend(search_harvard_librarycloud(query, limit=min(per_source, 50), page=page))
        except Exception as exc:
            results.append(_error_row("harvard_librarycloud", "Harvard University", exc))

    if "europe_pmc" in targets:
        try:
            results.extend(search_europe_pmc(query, limit=per_source, page=page))
        except Exception as exc:
            results.append(_error_row("europe_pmc", "Europe PMC", exc))

    if "doaj" in targets:
        try:
            results.extend(search_doaj_articles(query, limit=min(per_source, 100), page=page))
        except Exception as exc:
            results.append(_error_row("doaj", "DOAJ", exc))

    deduped = []
    seen = set()
    for row in results:
        key = row.get("open_access_url") or row.get("source_url") or row.get("external_id") or row.get("title")
        if not key or key in seen:
            continue
        seen.add(key)
        deduped.append(row)
    return deduped
