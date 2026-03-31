from __future__ import annotations

from pathlib import Path
from datetime import datetime
import json
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
STATE_DIR = PROJECT_ROOT / "data" / "app_state"
STATE_DIR.mkdir(parents=True, exist_ok=True)

WORKSPACE_FILE = STATE_DIR / "workspace_state.json"


def _load_json(path: Path, default: Any):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _save_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _now() -> str:
    return datetime.utcnow().isoformat()


def _empty_workspace(user_id: str) -> dict:
    return {
        "user_id": user_id,
        "saved_papers": [],
        "notes": [],
        "draft_sections": [],
        "reading_queue": [],
        "favorites": [],
        "updated_at": _now(),
    }


def get_workspace(user_id: str) -> dict:
    data = _load_json(WORKSPACE_FILE, {})
    return data.get(user_id, _empty_workspace(user_id))


def save_workspace(user_id: str, workspace: dict) -> dict:
    data = _load_json(WORKSPACE_FILE, {})
    workspace["updated_at"] = _now()
    data[user_id] = workspace
    _save_json(WORKSPACE_FILE, data)
    return workspace


def add_saved_paper(user_id: str, paper: dict) -> dict:
    ws = get_workspace(user_id)
    existing_ids = {p.get("work_id") for p in ws["saved_papers"]}
    if paper.get("work_id") not in existing_ids:
        ws["saved_papers"].append({
            **paper,
            "saved_at": _now(),
        })
    return save_workspace(user_id, ws)


def add_to_reading_queue(user_id: str, paper: dict) -> dict:
    ws = get_workspace(user_id)
    existing_ids = {p.get("work_id") for p in ws["reading_queue"]}
    if paper.get("work_id") not in existing_ids:
        ws["reading_queue"].append({
            **paper,
            "queued_at": _now(),
        })
    return save_workspace(user_id, ws)


def add_favorite(user_id: str, paper: dict) -> dict:
    ws = get_workspace(user_id)
    existing_ids = {p.get("work_id") for p in ws["favorites"]}
    if paper.get("work_id") not in existing_ids:
        ws["favorites"].append({
            **paper,
            "favorited_at": _now(),
        })
    return save_workspace(user_id, ws)


def add_note(user_id: str, note: dict) -> dict:
    ws = get_workspace(user_id)
    ws["notes"].append({
        "note_id": f"note_{len(ws['notes']) + 1}",
        "paper_work_id": note.get("paper_work_id"),
        "paper_title": note.get("paper_title"),
        "content": note.get("content", ""),
        "tags": note.get("tags", []),
        "created_at": _now(),
    })
    return save_workspace(user_id, ws)


def add_draft_section(user_id: str, section: dict) -> dict:
    ws = get_workspace(user_id)
    ws["draft_sections"].append({
        "section_id": f"section_{len(ws['draft_sections']) + 1}",
        "title": section.get("title", "Untitled Section"),
        "content": section.get("content", ""),
        "sources": section.get("sources", []),
        "created_at": _now(),
    })
    return save_workspace(user_id, ws)


def remove_saved_paper(user_id: str, work_id: str) -> dict:
    ws = get_workspace(user_id)
    ws["saved_papers"] = [p for p in ws["saved_papers"] if p.get("work_id") != work_id]
    ws["reading_queue"] = [p for p in ws["reading_queue"] if p.get("work_id") != work_id]
    ws["favorites"] = [p for p in ws["favorites"] if p.get("work_id") != work_id]
    return save_workspace(user_id, ws)
