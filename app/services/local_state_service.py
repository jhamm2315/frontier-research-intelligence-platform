from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from app.config import PLAN_MAP, PLANS
from app.services.workspace_service import get_workspace


PROJECT_ROOT = Path(__file__).resolve().parents[2]
STATE_DIR = PROJECT_ROOT / "data" / "app_state"
STATE_DIR.mkdir(parents=True, exist_ok=True)

LOCAL_PROFILES_FILE = STATE_DIR / "local_profiles.json"
LOCAL_COMPARISONS_FILE = STATE_DIR / "local_comparisons.json"
LOCAL_ADMIN_ROLE_AUDIT_FILE = STATE_DIR / "admin_role_audit_events.json"


def _load_json(path: Path, default: Any):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _save_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _now() -> str:
    return datetime.utcnow().isoformat()


def _default_profile(user_id: str) -> dict[str, Any]:
    return {
        "id": f"local_{user_id}",
        "clerk_user_id": user_id,
        "email": None,
        "full_name": user_id.replace("_", " ").title(),
        "first_name": None,
        "last_name": None,
        "avatar_url": None,
        "plan": "free",
        "auth_provider": "local",
        "is_admin": False,
        "created_at": _now(),
        "updated_at": _now(),
    }


def get_local_profile(clerk_user_id: str) -> dict[str, Any] | None:
    profiles = _load_json(LOCAL_PROFILES_FILE, {})
    return profiles.get(clerk_user_id)


def create_or_update_local_profile(payload: dict[str, Any]) -> dict[str, Any]:
    clerk_user_id = payload["clerk_user_id"]
    profiles = _load_json(LOCAL_PROFILES_FILE, {})
    existing = profiles.get(clerk_user_id, _default_profile(clerk_user_id))
    merged = {**existing, **payload, "updated_at": _now()}
    profiles[clerk_user_id] = merged
    _save_json(LOCAL_PROFILES_FILE, profiles)
    return merged


def set_local_profile_admin(clerk_user_id: str, is_admin: bool) -> dict[str, Any]:
    profile = get_local_profile(clerk_user_id) or _default_profile(clerk_user_id)
    return create_or_update_local_profile({
        **profile,
        "clerk_user_id": clerk_user_id,
        "is_admin": bool(is_admin),
    })


def list_local_profiles(limit: int = 25) -> list[dict[str, Any]]:
    profiles = list(_load_json(LOCAL_PROFILES_FILE, {}).values())
    profiles.sort(key=lambda row: row.get("updated_at", ""), reverse=True)
    return profiles[:limit]


def get_local_comparisons(user_id: str) -> list[dict[str, Any]]:
    payload = _load_json(LOCAL_COMPARISONS_FILE, {})
    rows = payload.get(user_id, [])
    rows.sort(key=lambda row: row.get("created_at", ""), reverse=True)
    return rows


def save_local_comparison(user_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    data = _load_json(LOCAL_COMPARISONS_FILE, {})
    rows = data.get(user_id, [])
    item = {
        "id": f"local_cmp_{len(rows) + 1}",
        "comparison_id": f"local_cmp_{len(rows) + 1}",
        "created_at": _now(),
        **payload,
    }
    rows.insert(0, item)
    data[user_id] = rows
    _save_json(LOCAL_COMPARISONS_FILE, data)
    return item


def delete_local_comparison(user_id: str, comparison_id: str) -> None:
    data = _load_json(LOCAL_COMPARISONS_FILE, {})
    rows = data.get(user_id, [])
    data[user_id] = [
        row
        for row in rows
        if row.get("id") != comparison_id and row.get("comparison_id") != comparison_id
    ]
    _save_json(LOCAL_COMPARISONS_FILE, data)


def log_local_admin_role_audit_event(payload: dict[str, Any]) -> dict[str, Any]:
    rows = _load_json(LOCAL_ADMIN_ROLE_AUDIT_FILE, [])
    item = {
        "id": f"local_role_audit_{len(rows) + 1}",
        "created_at": _now(),
        **payload,
    }
    rows.insert(0, item)
    _save_json(LOCAL_ADMIN_ROLE_AUDIT_FILE, rows[:500])
    return item


def list_local_admin_role_audit_events(limit: int = 50) -> list[dict[str, Any]]:
    rows = _load_json(LOCAL_ADMIN_ROLE_AUDIT_FILE, [])
    rows.sort(key=lambda row: row.get("created_at", ""), reverse=True)
    return rows[: max(1, min(limit, 200))]


def fallback_subscription_plans() -> list[dict[str, Any]]:
    return [
        {
            "code": plan.code,
            "name": plan.name,
            "price_label": plan.price,
            "headline": plan.tagline,
            "description": plan.description,
        }
        for plan in PLANS
        if plan.code != "free"
    ]


def build_local_customer_profile(clerk_user_id: str) -> dict[str, Any]:
    profile = get_local_profile(clerk_user_id) or _default_profile(clerk_user_id)
    workspace = get_workspace(clerk_user_id)
    saved_papers = workspace.get("saved_papers", [])
    favorites = workspace.get("favorites", [])
    reading_queue = workspace.get("reading_queue", [])
    notes = workspace.get("notes", [])

    topics: dict[str, int] = {}
    for row in saved_papers + favorites + reading_queue:
        topic = (row.get("topic") or row.get("primary_topic") or "").strip()
        if topic:
            topics[topic] = topics.get(topic, 0) + 1

    top_topics = [
        {"topic": topic, "score": score}
        for topic, score in sorted(topics.items(), key=lambda item: (-item[1], item[0]))[:5]
    ]
    plan_code = profile.get("plan") or "free"
    upgrade = {
        "free": "student",
        "student": "pro",
        "pro": "enterprise",
        "enterprise": None,
    }.get(plan_code)

    return {
        "profile": profile,
        "customer": {
            "profile_id": profile["id"],
            "clerk_user_id": clerk_user_id,
            "plan_code": plan_code,
            "lifecycle_stage": "active" if saved_papers or notes else "new",
            "engagement_status": "active" if reading_queue or favorites else "new",
        },
        "sales_profile": {
            "current_plan": plan_code,
            "recommended_upgrade_plan": upgrade,
            "top_topics": top_topics,
            "recent_activity": [
                {
                    "event_type": "save",
                    "title": row.get("title"),
                    "topic": row.get("topic") or row.get("primary_topic"),
                    "created_at": row.get("saved_at"),
                }
                for row in saved_papers[:5]
            ],
            "usage_totals": {
                "total_saved_papers": len(saved_papers),
                "total_favorites": len(favorites),
                "total_queue_items": len(reading_queue),
                "total_notes": len(notes),
            },
        },
    }


def build_local_dashboard_overview(days: int = 30) -> dict[str, Any]:
    profiles = list_local_profiles(limit=250)
    customer_profiles = [build_local_customer_profile(row["clerk_user_id"]) for row in profiles]
    plan_mix: dict[str, int] = {}
    for item in customer_profiles:
        plan_code = item["customer"]["plan_code"]
        plan_mix[plan_code] = plan_mix.get(plan_code, 0) + 1

    upgrade_candidates = [
        {
            "clerk_user_id": item["customer"]["clerk_user_id"],
            "plan_code": item["customer"]["plan_code"],
            "recommended_upgrade_plan": item["sales_profile"]["recommended_upgrade_plan"],
            "top_topics": item["sales_profile"]["top_topics"],
        }
        for item in customer_profiles
        if item["sales_profile"]["recommended_upgrade_plan"]
    ][:10]

    return {
        "mode": "local_fallback",
        "days": days,
        "kpis": {
            "active_customers": len(customer_profiles),
            "active_subscriptions": sum(1 for item in customer_profiles if item["customer"]["plan_code"] != "free"),
            "revenue_cents": 0,
            "tracked_profiles": len(profiles),
        },
        "plan_mix": [
            {
                "plan_code": plan_code,
                "customer_count": count,
                "plan_name": PLAN_MAP.get(plan_code).name if plan_code in PLAN_MAP else plan_code.title(),
            }
            for plan_code, count in sorted(plan_mix.items())
        ],
        "upgrade_candidates": upgrade_candidates,
        "recent_transactions": [],
    }
