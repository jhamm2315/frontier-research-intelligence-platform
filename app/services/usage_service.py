from __future__ import annotations

from pathlib import Path
from datetime import datetime
import json
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
STATE_DIR = PROJECT_ROOT / "data" / "app_state"
STATE_DIR.mkdir(parents=True, exist_ok=True)

USAGE_FILE = STATE_DIR / "usage_tracking.json"

DEFAULT_LIMITS = {
    "free": {
        "searches_per_day": 20,
        "arxiv_ingests_per_day": 5,
        "questions_per_day": 10,
        "uploads_per_day": 3,
        "workspace_projects": 3,
    },
    "pro": {
        "searches_per_day": 500,
        "arxiv_ingests_per_day": 100,
        "questions_per_day": 250,
        "uploads_per_day": 100,
        "workspace_projects": 100,
    },
    "research": {
        "searches_per_day": 5000,
        "arxiv_ingests_per_day": 1000,
        "questions_per_day": 2000,
        "uploads_per_day": 1000,
        "workspace_projects": 1000,
    },
}


def _load_json(path: Path, default: Any):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _save_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _today_key() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d")


def _get_user_bucket(user_id: str) -> dict:
    data = _load_json(USAGE_FILE, {})
    return data.get(user_id, {})


def _save_user_bucket(user_id: str, bucket: dict) -> None:
    data = _load_json(USAGE_FILE, {})
    data[user_id] = bucket
    _save_json(USAGE_FILE, data)


def get_plan_limits(plan: str) -> dict:
    return DEFAULT_LIMITS.get(plan, DEFAULT_LIMITS["free"])


def get_today_usage(user_id: str) -> dict:
    bucket = _get_user_bucket(user_id)
    day_key = _today_key()
    return bucket.get(day_key, {
        "searches": 0,
        "arxiv_ingests": 0,
        "questions": 0,
        "uploads": 0,
    })


def increment_usage(user_id: str, usage_type: str, amount: int = 1) -> dict:
    valid_types = {"searches", "arxiv_ingests", "questions", "uploads"}
    if usage_type not in valid_types:
        raise ValueError(f"Unsupported usage type: {usage_type}")

    bucket = _get_user_bucket(user_id)
    day_key = _today_key()

    if day_key not in bucket:
        bucket[day_key] = {
            "searches": 0,
            "arxiv_ingests": 0,
            "questions": 0,
            "uploads": 0,
        }

    bucket[day_key][usage_type] += amount
    _save_user_bucket(user_id, bucket)
    return bucket[day_key]


def get_usage_snapshot(user_id: str, plan: str = "free") -> dict:
    usage = get_today_usage(user_id)
    limits = get_plan_limits(plan)
    return {
        "user_id": user_id,
        "plan": plan,
        "date": _today_key(),
        "usage": usage,
        "limits": limits,
        "remaining": {
            "searches_per_day": max(limits["searches_per_day"] - usage["searches"], 0),
            "arxiv_ingests_per_day": max(limits["arxiv_ingests_per_day"] - usage["arxiv_ingests"], 0),
            "questions_per_day": max(limits["questions_per_day"] - usage["questions"], 0),
            "uploads_per_day": max(limits["uploads_per_day"] - usage["uploads"], 0),
        },
    }


def can_use_feature(user_id: str, feature: str, plan: str = "free") -> tuple[bool, dict]:
    """
    feature:
      - searches
      - arxiv_ingests
      - questions
      - uploads
    """
    usage = get_today_usage(user_id)
    limits = get_plan_limits(plan)

    mapping = {
        "searches": "searches_per_day",
        "arxiv_ingests": "arxiv_ingests_per_day",
        "questions": "questions_per_day",
        "uploads": "uploads_per_day",
    }

    if feature not in mapping:
        raise ValueError(f"Unsupported feature: {feature}")

    usage_key = feature
    limit_key = mapping[feature]

    allowed = usage.get(usage_key, 0) < limits[limit_key]
    return allowed, {
        "feature": feature,
        "current": usage.get(usage_key, 0),
        "limit": limits[limit_key],
        "remaining": max(limits[limit_key] - usage.get(usage_key, 0), 0),
        "plan": plan,
    }


def enforce_usage_limit(user_id: str, feature: str, plan: str = "free") -> dict:
    allowed, detail = can_use_feature(user_id, feature, plan)
    if not allowed:
        raise PermissionError(
            f"{feature} limit reached for plan '{plan}'. "
            f"Used {detail['current']} of {detail['limit']} today."
        )
    return detail

def is_admin_user(profile):
    return profile.get("is_admin") is True
