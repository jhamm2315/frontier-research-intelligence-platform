from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from app.services.business_ops_service import record_profile_activity
from app.services.persistence_service import get_profile_by_clerk_user_id
from app.services.supabase_service import get_supabase


EVENT_WEIGHTS: Dict[str, float] = {
    "search": 1.0,
    "view": 2.0,
    "save": 5.0,
    "queue": 4.0,
    "favorite": 6.0,
    "compare": 4.0,
    "note": 5.0,
    "question": 4.0,
    "upload": 3.0,
}

PAPER_COUNTERS: Dict[str, str] = {
    "search": "search_count",
    "view": "view_count",
    "save": "save_count",
    "queue": "queue_count",
    "favorite": "favorite_count",
    "compare": "compare_count",
    "note": "note_count",
    "question": "question_count",
    "upload": "upload_count",
}

TOPIC_COUNTERS: Dict[str, str] = {
    "search": "search_count",
    "save": "save_count",
    "compare": "compare_count",
    "question": "question_count",
}

EXCLUDED_METADATA_KEYS = {
    "content",
    "text",
    "raw_text",
    "document_text",
    "answer",
    "evidence",
    "summary",
    "plain_english_summary",
    "academic_summary",
    "executive_summary",
    "technical_summary",
    "methods_summary",
    "results_summary",
    "limitations_summary",
    "conclusion_summary",
    "practical_applications",
    "citation_guidance",
}


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _clean_text(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _normalize_work_id(payload: Dict[str, Any]) -> Optional[str]:
    for key in ("work_id", "paper_work_id", "matched_work_id", "document_id", "paper_document_id"):
        value = _clean_text(payload.get(key))
        if value:
            return value
    return None


def _normalize_document_id(payload: Dict[str, Any]) -> Optional[str]:
    for key in ("document_id", "paper_document_id", "matched_document_id"):
        value = _clean_text(payload.get(key))
        if value:
            return value
    return None


def _normalize_title(payload: Dict[str, Any]) -> Optional[str]:
    for key in ("title", "paper_title", "file_name"):
        value = _clean_text(payload.get(key))
        if value:
            return value
    return None


def _normalize_topic(payload: Dict[str, Any]) -> Optional[str]:
    for key in ("topic", "primary_topic"):
        value = _clean_text(payload.get(key))
        if value:
            return value
    return None


def _sanitize_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, str):
        return value[:500]
    if isinstance(value, list):
        return [_sanitize_value(item) for item in value[:10]]
    if isinstance(value, dict):
        cleaned: Dict[str, Any] = {}
        for key, item in value.items():
            if key in EXCLUDED_METADATA_KEYS:
                continue
            cleaned[key] = _sanitize_value(item)
        return cleaned
    return str(value)[:500]


def _sanitize_metadata(payload: Dict[str, Any]) -> Dict[str, Any]:
    cleaned: Dict[str, Any] = {}
    for key, value in payload.items():
        if key in EXCLUDED_METADATA_KEYS:
            continue
        cleaned[key] = _sanitize_value(value)
    return cleaned


def _build_event_row(profile_id: str, event_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    metadata = _sanitize_metadata(payload)

    return {
        "profile_id": profile_id,
        "event_type": event_type,
        "event_source": _clean_text(payload.get("event_source")) or "api",
        "action_context": _clean_text(payload.get("action_context")),
        "search_query": _clean_text(payload.get("search_query") or payload.get("query")),
        "search_mode": _clean_text(payload.get("search_mode")),
        "work_id": _normalize_work_id(payload),
        "document_id": _normalize_document_id(payload),
        "title": _normalize_title(payload),
        "source_system": _clean_text(payload.get("source_system")),
        "author": _clean_text(payload.get("author")),
        "institution": _clean_text(payload.get("institution")),
        "topic": _normalize_topic(payload),
        "result_count": payload.get("result_count"),
        "result_rank": payload.get("result_rank"),
        "event_value": float(payload.get("event_value") or EVENT_WEIGHTS.get(event_type, 1.0)),
        "recommendation_context": _sanitize_value(payload.get("recommendation_context") or {}) or {},
        "metadata": metadata,
    }


def _get_existing_row(table_name: str, **filters: Any) -> Optional[Dict[str, Any]]:
    sb = get_supabase()
    query = sb.table(table_name).select("*")
    for key, value in filters.items():
        query = query.eq(key, value)
    result = query.limit(1).execute()
    return result.data[0] if result.data else None


def _merge_json(existing: Any, updates: Any) -> Dict[str, Any]:
    merged: Dict[str, Any] = {}
    if isinstance(existing, dict):
        merged.update(existing)
    if isinstance(updates, dict):
        merged.update(updates)
    return merged


def _upsert_profile_paper_interest(event_row: Dict[str, Any]) -> None:
    work_id = event_row.get("work_id")
    if not work_id:
        return

    profile_id = event_row["profile_id"]
    now = _utcnow()
    existing = _get_existing_row("profile_paper_interests", profile_id=profile_id, work_id=work_id)
    row = existing.copy() if existing else {}

    row.update({
        "profile_id": profile_id,
        "work_id": work_id,
        "document_id": event_row.get("document_id") or row.get("document_id"),
        "title": event_row.get("title") or row.get("title"),
        "source_system": event_row.get("source_system") or row.get("source_system"),
        "author": event_row.get("author") or row.get("author"),
        "institution": event_row.get("institution") or row.get("institution"),
        "topic": event_row.get("topic") or row.get("topic"),
        "first_interaction_at": row.get("first_interaction_at") or now,
        "last_interaction_at": now,
        "last_event_type": event_row.get("event_type"),
        "last_search_query": event_row.get("search_query") or row.get("last_search_query"),
        "recommendation_score": float(row.get("recommendation_score") or 0) + float(event_row.get("event_value") or 0),
        "metadata": _merge_json(row.get("metadata"), event_row.get("metadata")),
    })

    for counter_name in PAPER_COUNTERS.values():
        row[counter_name] = int(row.get(counter_name) or 0)

    counter = PAPER_COUNTERS.get(event_row.get("event_type", ""))
    if counter:
        row[counter] += 1

    get_supabase().table("profile_paper_interests").upsert(row, on_conflict="profile_id,work_id").execute()


def _upsert_profile_topic_interest(event_row: Dict[str, Any]) -> None:
    topic = event_row.get("topic")
    if not topic:
        return

    profile_id = event_row["profile_id"]
    now = _utcnow()
    existing = _get_existing_row("profile_topic_interests", profile_id=profile_id, topic=topic)
    row = existing.copy() if existing else {}

    row.update({
        "profile_id": profile_id,
        "topic": topic,
        "last_interaction_at": now,
        "recommendation_score": float(row.get("recommendation_score") or 0) + float(event_row.get("event_value") or 0),
        "metadata": _merge_json(
            row.get("metadata"),
            {
                "last_title": event_row.get("title"),
                "last_source_system": event_row.get("source_system"),
            },
        ),
    })

    row["interaction_count"] = int(row.get("interaction_count") or 0) + 1

    for counter_name in TOPIC_COUNTERS.values():
        row[counter_name] = int(row.get(counter_name) or 0)

    counter = TOPIC_COUNTERS.get(event_row.get("event_type", ""))
    if counter:
        row[counter] += 1

    get_supabase().table("profile_topic_interests").upsert(row, on_conflict="profile_id,topic").execute()


def track_recommendation_activity(profile_id: str, event_type: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    event_row = _build_event_row(profile_id, event_type, payload)
    result = get_supabase().table("paper_activity_events").insert(event_row).execute()
    _upsert_profile_paper_interest(event_row)
    _upsert_profile_topic_interest(event_row)
    record_profile_activity(profile_id, event_type, event_row)
    return result.data[0] if result.data else event_row


def track_recommendation_activity_for_user(
    clerk_user_id: Optional[str],
    event_type: str,
    payload: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    if not clerk_user_id:
        return None

    profile = get_profile_by_clerk_user_id(clerk_user_id)
    if not profile:
        return None

    return track_recommendation_activity(profile["id"], event_type, payload)


def safe_track_recommendation_activity(profile_id: str, event_type: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    try:
        return track_recommendation_activity(profile_id, event_type, payload)
    except Exception:
        return None


def safe_track_recommendation_activity_for_user(
    clerk_user_id: Optional[str],
    event_type: str,
    payload: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    try:
        return track_recommendation_activity_for_user(clerk_user_id, event_type, payload)
    except Exception:
        return None
