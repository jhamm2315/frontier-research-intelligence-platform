import json
from typing import List, Dict, Any

from app.services.local_llm_service import generate_local_llm_summary

from app.services.local_llm_service import generate_local_llm_summary


def _get_paper_detail_by_work_id(work_id: str) -> dict:
    """
    Runtime compatibility loader.

    This project does not currently have app.services.research_service,
    so we resolve the paper-detail function from app.api.research
    after imports are completed.
    """
    from app.api import research as research_api

    candidate_names = [
        "get_paper_detail_by_work_id",
        "get_paper_detail",
        "get_paper",
        "paper_detail",
        "paper_details",
        "get_paper_route",
    ]

    for name in candidate_names:
        fn = getattr(research_api, name, None)
        if callable(fn):
            result = fn(work_id)
            if isinstance(result, dict):
                return result

    raise RuntimeError(
        "Could not resolve a paper detail loader from app.api.research. "
        "Expected one of: get_paper_detail_by_work_id, get_paper_detail, "
        "get_paper, paper_detail, paper_details, get_paper_route."
    )

def _safe_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _build_paper_context(work_id: str) -> Dict[str, Any]:
    paper =_get_paper_detail_by_work_id(work_id)

    metadata = paper.get("metadata", {}) or {}
    ai_summary = paper.get("ai_summary", {}) or {}

    return {
        "work_id": work_id,
        "title": _safe_text(metadata.get("title")),
        "author": _safe_text(metadata.get("author")),
        "institution": _safe_text(metadata.get("institution")),
        "topic": _safe_text(metadata.get("topic") or metadata.get("primary_topic")),
        "publication_year": _safe_text(metadata.get("publication_year")),
        "citation": _safe_text(metadata.get("citation")),
        "plain_english_summary": _safe_text(ai_summary.get("plain_english_summary")),
        "academic_summary": _safe_text(ai_summary.get("academic_summary")),
        "methods_summary": _safe_text(ai_summary.get("methods_summary")),
        "results_summary": _safe_text(ai_summary.get("results_summary")),
        "limitations_summary": _safe_text(ai_summary.get("limitations_summary")),
        "practical_applications": _safe_text(ai_summary.get("practical_applications")),
        "suggested_topics": _safe_text(ai_summary.get("suggested_topics")),
    }


def compare_papers(work_ids: List[str], user_question: str = "") -> Dict[str, Any]:
    papers = [_build_paper_context(work_id) for work_id in work_ids]

    comparison_payload = {
        "papers": papers,
        "user_question": user_question or "Compare these papers across topic, methods, findings, limitations, and practical applications."
    }

    prompt = f"""
You are an academic research comparison assistant.

Compare the following papers and return a structured response in JSON.

Input:
{json.dumps(comparison_payload, indent=2)}

Return valid JSON with this exact structure:
{{
  "comparison_summary": "...",
  "common_themes": ["...", "..."],
  "key_differences": ["...", "..."],
  "methods_comparison": "...",
  "results_comparison": "...",
  "limitations_comparison": "...",
  "best_for_students": "...",
  "best_for_researchers": "...",
  "best_for_practical_use": "...",
  "recommended_paper": {{
    "work_id": "...",
    "reason": "..."
  }}
}}

Rules:
- Be concise but informative
- Use only the provided information
- If some values are missing, say so clearly
- Return JSON only
"""

    raw_response = generate_local_llm_summary(prompt)

    try:
        parsed = json.loads(raw_response)
    except Exception:
        parsed = {
            "comparison_summary": raw_response,
            "common_themes": [],
            "key_differences": [],
            "methods_comparison": "Could not structure methods comparison.",
            "results_comparison": "Could not structure results comparison.",
            "limitations_comparison": "Could not structure limitations comparison.",
            "best_for_students": "Not available.",
            "best_for_researchers": "Not available.",
            "best_for_practical_use": "Not available.",
            "recommended_paper": {
                "work_id": papers[0]["work_id"] if papers else "",
                "reason": "Fallback response because structured JSON parsing failed."
            }
        }

    return {
        "papers": papers,
        "comparison": parsed
    }
