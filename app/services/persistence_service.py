from typing import Any, Dict, List, Optional
from app.services.supabase_service import get_supabase


def get_profile_by_clerk_user_id(clerk_user_id: str) -> Optional[Dict[str, Any]]:
    sb = get_supabase()
    res = (
        sb.table("profiles")
        .select("*")
        .eq("clerk_user_id", clerk_user_id)
        .limit(1)
        .execute()
    )
    return res.data[0] if res.data else None


def create_or_update_profile(payload: Dict[str, Any]) -> Dict[str, Any]:
    sb = get_supabase()
    existing = get_profile_by_clerk_user_id(payload["clerk_user_id"])

    if existing:
        res = (
            sb.table("profiles")
            .update(payload)
            .eq("clerk_user_id", payload["clerk_user_id"])
            .execute()
        )
    else:
        res = sb.table("profiles").insert(payload).execute()

    return res.data[0]


def list_profiles(limit: int = 50, search: str | None = None) -> List[Dict[str, Any]]:
    sb = get_supabase()
    safe_limit = max(1, min(limit, 200))
    res = (
        sb.table("profiles")
        .select("*")
        .order("updated_at", desc=True)
        .limit(safe_limit)
        .execute()
    )
    rows = res.data or []
    if search:
        needle = search.strip().lower()
        rows = [
            row for row in rows
            if needle in str(row.get("clerk_user_id", "")).lower()
            or needle in str(row.get("email", "")).lower()
            or needle in str(row.get("full_name", "")).lower()
        ]
    return rows


def update_profile_admin_flag(clerk_user_id: str, is_admin: bool) -> Dict[str, Any]:
    sb = get_supabase()
    existing = get_profile_by_clerk_user_id(clerk_user_id)
    if not existing:
        raise ValueError("Profile not found")
    res = (
        sb.table("profiles")
        .update({"is_admin": is_admin})
        .eq("clerk_user_id", clerk_user_id)
        .execute()
    )
    return res.data[0]


def get_saved_papers(profile_id: str) -> List[Dict[str, Any]]:
    sb = get_supabase()
    res = (
        sb.table("saved_papers")
        .select("*")
        .eq("profile_id", profile_id)
        .order("created_at", desc=True)
        .execute()
    )
    return res.data or []


def save_paper(profile_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    sb = get_supabase()
    row = {
        "profile_id": profile_id,
        "work_id": payload.get("work_id"),
        "document_id": payload.get("document_id"),
        "title": payload.get("title"),
        "source_system": payload.get("source_system"),
        "institution": payload.get("institution"),
        "author": payload.get("author"),
        "topic": payload.get("topic"),
        "citation": payload.get("citation"),
        "published": str(payload.get("published") or payload.get("publication_year") or ""),
        "pdf_url": payload.get("pdf_url"),
        "entry_url": payload.get("entry_url"),
        "metadata": payload,
    }
    res = sb.table("saved_papers").upsert(row, on_conflict="profile_id,work_id").execute()
    return res.data[0]


def delete_saved_paper(profile_id: str, work_id: str) -> None:
    sb = get_supabase()
    sb.table("saved_papers").delete().eq("profile_id", profile_id).eq("work_id", work_id).execute()


def get_reading_queue(profile_id: str) -> List[Dict[str, Any]]:
    sb = get_supabase()
    res = (
        sb.table("reading_queue")
        .select("*")
        .eq("profile_id", profile_id)
        .order("created_at", desc=True)
        .execute()
    )
    return res.data or []


def queue_paper(profile_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    sb = get_supabase()
    row = {
        "profile_id": profile_id,
        "work_id": payload.get("work_id"),
        "document_id": payload.get("document_id"),
        "title": payload.get("title"),
        "source_system": payload.get("source_system"),
        "institution": payload.get("institution"),
    }
    res = sb.table("reading_queue").upsert(row, on_conflict="profile_id,work_id").execute()
    return res.data[0]


def get_favorites(profile_id: str) -> List[Dict[str, Any]]:
    sb = get_supabase()
    res = (
        sb.table("favorite_papers")
        .select("*")
        .eq("profile_id", profile_id)
        .order("created_at", desc=True)
        .execute()
    )
    return res.data or []


def favorite_paper(profile_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    sb = get_supabase()
    row = {
        "profile_id": profile_id,
        "work_id": payload.get("work_id"),
        "document_id": payload.get("document_id"),
        "title": payload.get("title"),
        "source_system": payload.get("source_system"),
        "institution": payload.get("institution"),
    }
    res = sb.table("favorite_papers").upsert(row, on_conflict="profile_id,work_id").execute()
    return res.data[0]


def add_note(profile_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    sb = get_supabase()
    row = {
        "profile_id": profile_id,
        "paper_work_id": payload.get("paper_work_id"),
        "paper_document_id": payload.get("paper_document_id"),
        "paper_title": payload.get("paper_title"),
        "content": payload.get("content"),
        "tags": payload.get("tags", []),
    }
    res = sb.table("paper_notes").insert(row).execute()
    return res.data[0]


def get_comparisons(profile_id: str) -> List[Dict[str, Any]]:
    sb = get_supabase()
    res = (
        sb.table("paper_comparisons")
        .select("*")
        .eq("profile_id", profile_id)
        .order("created_at", desc=True)
        .execute()
    )
    return res.data or []


def save_comparison(profile_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    sb = get_supabase()
    row = {
        "profile_id": profile_id,
        "title": payload.get("title"),
        "work_ids": payload.get("work_ids", []),
        "paper_titles": payload.get("paper_titles", []),
        "question": payload.get("question"),
        "summary": payload.get("summary"),
    }
    res = sb.table("paper_comparisons").insert(row).execute()
    return res.data[0]


def delete_comparison(profile_id: str, comparison_id: str) -> None:
    sb = get_supabase()
    sb.table("paper_comparisons").delete().eq("profile_id", profile_id).eq("id", comparison_id).execute()


def upsert_open_access_source(payload: Dict[str, Any]) -> Dict[str, Any]:
    sb = get_supabase()
    res = sb.table("open_access_sources").upsert(payload, on_conflict="source_key").execute()
    return res.data[0]


def upsert_open_access_source_assets(source_id: str, assets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not assets:
        return []

    sb = get_supabase()
    rows = []
    for asset in assets:
        rows.append({
            "source_id": source_id,
            "asset_type": asset.get("asset_type") or "reference",
            "label": asset.get("label"),
            "asset_url": asset.get("asset_url"),
            "mime_type": asset.get("mime_type"),
            "is_primary": bool(asset.get("is_primary")),
            "metadata": asset.get("metadata") or {},
        })

    res = sb.table("open_access_source_assets").upsert(
        rows,
        on_conflict="source_id,asset_url",
    ).execute()
    return res.data or []


def log_open_access_ingestion_run(payload: Dict[str, Any]) -> Dict[str, Any]:
    sb = get_supabase()
    res = sb.table("open_access_ingestion_runs").insert(payload).execute()
    return res.data[0]


def log_admin_role_audit_event(payload: Dict[str, Any]) -> Dict[str, Any]:
    sb = get_supabase()
    res = sb.table("admin_role_audit_events").insert(payload).execute()
    return res.data[0]


def list_admin_role_audit_events(limit: int = 50) -> List[Dict[str, Any]]:
    sb = get_supabase()
    safe_limit = max(1, min(limit, 200))
    res = (
        sb.table("admin_role_audit_events")
        .select("*")
        .order("created_at", desc=True)
        .limit(safe_limit)
        .execute()
    )
    return res.data or []


def get_runtime_setting(key: str) -> Optional[Dict[str, Any]]:
    sb = get_supabase()
    res = (
        sb.table("app_runtime_settings")
        .select("*")
        .eq("key", key)
        .limit(1)
        .execute()
    )
    return res.data[0] if res.data else None


def upsert_runtime_setting(key: str, value: Dict[str, Any], updated_by_clerk_user_id: str | None = None) -> Dict[str, Any]:
    sb = get_supabase()
    res = sb.table("app_runtime_settings").upsert({
        "key": key,
        "value": value,
        "updated_by_clerk_user_id": updated_by_clerk_user_id,
    }, on_conflict="key").execute()
    return res.data[0]


def get_featured_open_access_sources(limit: int = 12) -> List[Dict[str, Any]]:
    sb = get_supabase()
    res = (
        sb.table("open_access_sources")
        .select("*, open_access_source_assets(*)")
        .eq("verification_status", "verified")
        .eq("is_featured", True)
        .order("last_verified_at", desc=True)
        .limit(limit)
        .execute()
    )
    return res.data or []
