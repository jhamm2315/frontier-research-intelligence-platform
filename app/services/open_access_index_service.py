from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from app.services.open_access_ingestion_service import search_verified_open_access_records
from app.services.persistence_service import (
    get_featured_open_access_sources,
    log_open_access_ingestion_run,
    upsert_open_access_source,
    upsert_open_access_source_assets,
)
from app.services.supabase_service import get_supabase


PROJECT_ROOT = Path(__file__).resolve().parents[2]
STATE_DIR = PROJECT_ROOT / "data" / "app_state"
STATE_DIR.mkdir(parents=True, exist_ok=True)
LOCAL_OPEN_ACCESS_SOURCES_FILE = STATE_DIR / "open_access_sources.json"
LOCAL_OPEN_ACCESS_RUNS_FILE = STATE_DIR / "open_access_ingestion_runs.json"


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_json(path: Path, default: Any):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _save_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _local_upsert_source(payload: dict[str, Any]) -> dict[str, Any]:
    rows = _load_json(LOCAL_OPEN_ACCESS_SOURCES_FILE, [])
    existing_index = next((idx for idx, row in enumerate(rows) if row.get("source_key") == payload.get("source_key")), None)
    source_id = payload.get("id") or payload.get("source_key")
    item = {
        **payload,
        "id": source_id,
        "open_access_source_assets": payload.get("open_access_source_assets", []),
        "updated_at": _utcnow_iso(),
    }
    if existing_index is None:
        item["created_at"] = item.get("created_at") or _utcnow_iso()
        rows.append(item)
    else:
        item["created_at"] = rows[existing_index].get("created_at") or _utcnow_iso()
        rows[existing_index] = item
    _save_json(LOCAL_OPEN_ACCESS_SOURCES_FILE, rows)
    return item


def _local_upsert_assets(source_id: str, assets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = _load_json(LOCAL_OPEN_ACCESS_SOURCES_FILE, [])
    for row in rows:
        if row.get("id") == source_id or row.get("source_key") == source_id:
            existing = row.get("open_access_source_assets", [])
            seen = {item.get("asset_url") for item in existing}
            for asset in assets:
                if asset.get("asset_url") not in seen:
                    existing.append({
                        "id": f"{source_id}:{len(existing) + 1}",
                        "source_id": source_id,
                        **asset,
                    })
                    seen.add(asset.get("asset_url"))
            row["open_access_source_assets"] = existing
            row["updated_at"] = _utcnow_iso()
            _save_json(LOCAL_OPEN_ACCESS_SOURCES_FILE, rows)
            return existing
    return []


def _local_log_run(payload: dict[str, Any]) -> dict[str, Any]:
    runs = _load_json(LOCAL_OPEN_ACCESS_RUNS_FILE, [])
    item = {
        "id": f"run_{len(runs) + 1}",
        "created_at": _utcnow_iso(),
        **payload,
    }
    runs.insert(0, item)
    _save_json(LOCAL_OPEN_ACCESS_RUNS_FILE, runs)
    return item


def _persist_source_record(record: dict[str, Any]) -> dict[str, Any]:
    row = record.copy()
    assets = row.pop("assets", [])
    try:
        source = upsert_open_access_source(row)
        persisted_assets = upsert_open_access_source_assets(source["id"], assets)
        source["open_access_source_assets"] = persisted_assets
        return source
    except Exception:
        source = _local_upsert_source(row)
        persisted_assets = _local_upsert_assets(source["id"], assets)
        source["open_access_source_assets"] = persisted_assets
        return source


def _persist_ingestion_run(payload: dict[str, Any]) -> dict[str, Any]:
    try:
        return log_open_access_ingestion_run(payload)
    except Exception:
        return _local_log_run(payload)


def collect_open_access_index(
    query: str,
    pages: int = 3,
    limit_per_source: int = 50,
    requested_by_clerk_user_id: str | None = None,
    mark_featured: bool = False,
    source_targets: tuple[str, ...] | None = None,
) -> dict[str, Any]:
    clean_query = " ".join(str(query or "").split()).strip()
    if not clean_query:
        raise ValueError("query is required for open-access indexing")

    pages = max(1, min(pages, 20))
    limit_per_source = max(1, min(limit_per_source, 100))

    persisted_sources: list[dict[str, Any]] = []
    warnings: list[str] = []
    seen_source_keys: set[str] = set()

    for page in range(1, pages + 1):
        try:
            records = search_verified_open_access_records(
                clean_query,
                limit_per_source=limit_per_source,
                page=page,
                source_targets=source_targets,
            )
        except Exception as exc:
            warnings.append(f"page {page}: {exc}")
            continue

        for record in records:
            if mark_featured:
                record["is_featured"] = True
            source_key = record.get("source_key")
            if source_key in seen_source_keys:
                continue
            seen_source_keys.add(source_key)
            try:
                persisted_sources.append(_persist_source_record(record))
            except Exception as exc:
                warnings.append(f"{source_key or 'unknown'}: {exc}")

    run = _persist_ingestion_run({
        "requested_by_clerk_user_id": requested_by_clerk_user_id,
        "connector_name": "open_access_bulk_index",
        "query": clean_query,
        "ingestion_method": "api_batch_index",
        "status": "completed" if persisted_sources else "failed",
        "record_count": len(persisted_sources),
        "warning_count": len(warnings),
        "warnings": warnings,
        "metadata": {
            "pages": pages,
            "limit_per_source": limit_per_source,
            "featured": mark_featured,
            "source_targets": list(source_targets or ()),
            "source_keys": [row.get("source_key") for row in persisted_sources[:100]],
        },
        "completed_at": _utcnow_iso(),
    })

    return {
        "success": bool(persisted_sources),
        "query": clean_query,
        "pages": pages,
        "limit_per_source": limit_per_source,
        "source_targets": list(source_targets or ()),
        "record_count": len(persisted_sources),
        "warning_count": len(warnings),
        "warnings": warnings,
        "sources": persisted_sources,
        "ingestion_run": run,
    }


def _search_local_sources(
    query: str,
    limit: int = 50,
    offset: int = 0,
    source_system: str | None = None,
    summary_ready_only: bool = False,
) -> list[dict[str, Any]]:
    rows = _load_json(LOCAL_OPEN_ACCESS_SOURCES_FILE, [])
    query_text = query.lower().strip()
    filtered = []
    for row in rows:
        haystack = " ".join([
            row.get("title", ""),
            row.get("abstract", ""),
            " ".join(row.get("authors", []) or []),
            " ".join(row.get("topics", []) or []),
            " ".join(row.get("keywords", []) or []),
            " ".join(row.get("institutions", []) or []),
        ]).lower()
        if query_text and query_text not in haystack:
            continue
        if source_system and row.get("source_system") != source_system:
            continue
        if summary_ready_only and not row.get("is_summary_ready"):
            continue
        filtered.append(row)
    filtered.sort(key=lambda row: (row.get("last_verified_at") or "", row.get("publication_year") or 0), reverse=True)
    return filtered[offset: offset + limit]


def search_indexed_open_access_sources(
    query: str,
    limit: int = 50,
    offset: int = 0,
    source_system: str | None = None,
    summary_ready_only: bool = False,
) -> list[dict[str, Any]]:
    try:
        sb = get_supabase()
        selector = "*, open_access_source_assets(*)"
        query_text = query.strip()
        req = (
            sb.table("open_access_sources")
            .select(selector)
            .eq("verification_status", "verified")
            .order("last_verified_at", desc=True)
            .range(offset, max(offset, offset + limit - 1))
        )
        if source_system:
            req = req.eq("source_system", source_system)
        if summary_ready_only:
            req = req.eq("is_summary_ready", True)
        if query_text:
            safe_query = query_text.replace(",", " ").replace("%", "")
            req = req.or_(f"title.ilike.%{safe_query}%,abstract.ilike.%{safe_query}%")
        response = req.execute()
        rows = response.data or []
        if not query_text:
            return rows
        return [
            row for row in rows
            if query_text in " ".join([
                str(row.get("title", "")),
                str(row.get("abstract", "")),
                " ".join(row.get("authors", []) or []),
                " ".join(row.get("topics", []) or []),
                " ".join(row.get("keywords", []) or []),
                " ".join(row.get("institutions", []) or []),
            ]).lower()
        ]
    except Exception:
        return _search_local_sources(
            query=query,
            limit=limit,
            offset=offset,
            source_system=source_system,
            summary_ready_only=summary_ready_only,
        )


def list_open_access_ingestion_runs(limit: int = 20) -> list[dict[str, Any]]:
    try:
        response = (
            get_supabase()
            .table("open_access_ingestion_runs")
            .select("*")
            .order("started_at", desc=True)
            .limit(limit)
            .execute()
        )
        return response.data or []
    except Exception:
        return _load_json(LOCAL_OPEN_ACCESS_RUNS_FILE, [])[:limit]


def get_featured_or_indexed_open_access_sources(limit: int = 12) -> list[dict[str, Any]]:
    try:
        rows = get_featured_open_access_sources(limit=limit)
        if rows:
            return rows
    except Exception:
        pass
    return _search_local_sources(query="", limit=limit, offset=0)
