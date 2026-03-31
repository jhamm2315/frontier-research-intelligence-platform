from __future__ import annotations

from dataclasses import asdict, replace
import json
from pathlib import Path
from typing import Any

from app.config import Settings
from app.services.persistence_service import get_runtime_setting, upsert_runtime_setting


PROJECT_ROOT = Path(__file__).resolve().parents[2]
STATE_DIR = PROJECT_ROOT / "data" / "app_state"
STATE_DIR.mkdir(parents=True, exist_ok=True)
SCHEDULER_OVERRIDES_FILE = STATE_DIR / "scheduler_overrides.json"
SCHEDULER_SETTING_KEY = "scheduler_config"

OVERRIDE_FIELDS = {
    "auto_index_enabled",
    "auto_index_pages",
    "auto_index_limit_per_source",
    "auto_index_queries",
    "auto_index_startup_delay_seconds",
    "auto_index_source_intervals",
    "auto_index_source_queries",
}


def _load_json(path: Path, default: Any):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _save_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def get_scheduler_overrides() -> dict[str, Any]:
    try:
        row = get_runtime_setting(SCHEDULER_SETTING_KEY)
        if row and isinstance(row.get("value"), dict):
            return row["value"]
    except Exception:
        pass
    payload = _load_json(SCHEDULER_OVERRIDES_FILE, {})
    return payload if isinstance(payload, dict) else {}


def save_scheduler_overrides(payload: dict[str, Any], updated_by_clerk_user_id: str | None = None) -> dict[str, Any]:
    clean: dict[str, Any] = {}
    for key, value in payload.items():
        if key not in OVERRIDE_FIELDS:
            continue
        if value is None:
            continue
        if key == "auto_index_queries":
            clean[key] = [str(item).strip() for item in value if str(item).strip()]
        elif key == "auto_index_source_intervals":
            clean[key] = {
                str(source).strip(): max(5, min(int(minutes), 10080))
                for source, minutes in (value or {}).items()
                if str(source).strip()
            }
        elif key == "auto_index_source_queries":
            clean[key] = {
                str(source).strip(): [str(item).strip() for item in queries if str(item).strip()]
                for source, queries in (value or {}).items()
                if str(source).strip()
            }
        else:
            clean[key] = value
    try:
        upsert_runtime_setting(
            SCHEDULER_SETTING_KEY,
            clean,
            updated_by_clerk_user_id=updated_by_clerk_user_id,
        )
    except Exception:
        _save_json(SCHEDULER_OVERRIDES_FILE, clean)
    return clean


def get_runtime_scheduler_settings(base: Settings) -> Settings:
    overrides = get_scheduler_overrides()
    patch: dict[str, Any] = {}
    for key, value in overrides.items():
        if key not in OVERRIDE_FIELDS:
            continue
        if key == "auto_index_queries":
            patch[key] = tuple(value)
        elif key == "auto_index_source_queries":
            patch[key] = {source: tuple(queries) for source, queries in value.items()}
        else:
            patch[key] = value
    return replace(base, **patch) if patch else base


def get_scheduler_admin_payload(base: Settings) -> dict[str, Any]:
    effective = get_runtime_scheduler_settings(base)
    return {
        "overrides": get_scheduler_overrides(),
        "effective": {
            **asdict(effective),
            "auto_index_queries": list(effective.auto_index_queries),
            "auto_index_source_queries": {
                key: list(value)
                for key, value in (effective.auto_index_source_queries or {}).items()
            },
        },
    }
