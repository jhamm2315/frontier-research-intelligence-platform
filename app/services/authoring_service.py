from __future__ import annotations

from pathlib import Path
from datetime import datetime
import json
from typing import Any

from app.services.citation_service import format_all_citations

PROJECT_ROOT = Path(__file__).resolve().parents[2]
STATE_DIR = PROJECT_ROOT / "data" / "app_state"
STATE_DIR.mkdir(parents=True, exist_ok=True)

AUTHORING_FILE = STATE_DIR / "authoring_projects.json"


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


def create_project(user_id: str, title: str, project_type: str = "white_paper") -> dict:
    data = _load_json(AUTHORING_FILE, {})
    user_projects = data.get(user_id, [])

    project = {
        "project_id": f"proj_{len(user_projects) + 1}",
        "user_id": user_id,
        "title": title,
        "project_type": project_type,  # white_paper, research_paper, research_brief
        "abstract": "",
        "outline": [],
        "sections": [],
        "sources": [],
        "citations": [],
        "created_at": _now(),
        "updated_at": _now(),
    }

    user_projects.append(project)
    data[user_id] = user_projects
    _save_json(AUTHORING_FILE, data)
    return project


def list_projects(user_id: str) -> list[dict]:
    data = _load_json(AUTHORING_FILE, {})
    return data.get(user_id, [])


def get_project(user_id: str, project_id: str) -> dict | None:
    projects = list_projects(user_id)
    for project in projects:
        if project["project_id"] == project_id:
            return project
    return None


def save_project(user_id: str, project: dict) -> dict:
    data = _load_json(AUTHORING_FILE, {})
    projects = data.get(user_id, [])

    for idx, item in enumerate(projects):
        if item["project_id"] == project["project_id"]:
            project["updated_at"] = _now()
            projects[idx] = project
            data[user_id] = projects
            _save_json(AUTHORING_FILE, data)
            return project

    projects.append(project)
    data[user_id] = projects
    _save_json(AUTHORING_FILE, data)
    return project


def add_section(user_id: str, project_id: str, section_title: str, content: str = "") -> dict:
    project = get_project(user_id, project_id)
    if not project:
        raise ValueError("Project not found")

    project["sections"].append({
        "section_id": f"sec_{len(project['sections']) + 1}",
        "title": section_title,
        "content": content,
        "created_at": _now(),
    })
    return save_project(user_id, project)


def add_source_to_project(user_id: str, project_id: str, paper_meta: dict) -> dict:
    project = get_project(user_id, project_id)
    if not project:
        raise ValueError("Project not found")

    existing_ids = {s.get("work_id") for s in project["sources"]}
    if paper_meta.get("work_id") not in existing_ids:
        project["sources"].append({
            **paper_meta,
            "added_at": _now(),
        })

        project["citations"].append({
            "work_id": paper_meta.get("work_id"),
            "title": paper_meta.get("title"),
            "formats": format_all_citations(paper_meta),
        })

    return save_project(user_id, project)


def update_project_abstract(user_id: str, project_id: str, abstract: str) -> dict:
    project = get_project(user_id, project_id)
    if not project:
        raise ValueError("Project not found")

    project["abstract"] = abstract
    return save_project(user_id, project)


def replace_working_draft(user_id: str, project_id: str, title: str, abstract: str, content: str) -> dict:
    project = get_project(user_id, project_id)
    if not project:
        raise ValueError("Project not found")

    project["title"] = title or project.get("title") or "Untitled Project"
    project["abstract"] = abstract
    project["sections"] = [{
        "section_id": "sec_1",
        "title": "Working Draft",
        "content": content,
        "created_at": project.get("created_at") or _now(),
    }]
    return save_project(user_id, project)


def render_project_markdown(user_id: str, project_id: str) -> str:
    project = get_project(user_id, project_id)
    if not project:
        raise ValueError("Project not found")

    lines = [f"# {project['title']}", ""]
    if project.get("abstract"):
        lines.extend(["## Abstract", project["abstract"], ""])

    for section in project.get("sections", []):
        lines.extend([f"## {section['title']}", section.get("content", ""), ""])

    if project.get("sources"):
        lines.extend(["## Sources", ""])
        for src in project["sources"]:
            lines.append(f"- {src.get('title', 'Untitled')}")

    if project.get("citations"):
        lines.extend(["", "## References", ""])
        for citation in project["citations"]:
            lines.append(f"- {citation['formats'].get('apa', '')}")

    return "\n".join(lines).strip()


def render_project_html(user_id: str, project_id: str) -> str:
    project = get_project(user_id, project_id)
    if not project:
        raise ValueError("Project not found")

    html_parts = [f"<h1>{project['title']}</h1>"]

    if project.get("abstract"):
        html_parts.append("<h2>Abstract</h2>")
        html_parts.append(f"<p>{project['abstract']}</p>")

    for section in project.get("sections", []):
        html_parts.append(f"<h2>{section['title']}</h2>")
        html_parts.append(f"<p>{section.get('content', '')}</p>")

    if project.get("sources"):
        html_parts.append("<h2>Sources</h2><ul>")
        for src in project["sources"]:
            html_parts.append(f"<li>{src.get('title', 'Untitled')}</li>")
        html_parts.append("</ul>")

    if project.get("citations"):
        html_parts.append("<h2>References</h2><ul>")
        for citation in project["citations"]:
            html_parts.append(f"<li>{citation['formats'].get('apa', '')}</li>")
        html_parts.append("</ul>")

    return "\n".join(html_parts)
