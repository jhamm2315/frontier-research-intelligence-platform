from pathlib import Path
import sys
import re
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from config.settings import PROCESSED_DIR
from app.services.summarization_service import summarize_text
from app.services.local_llm_service import generate_paper_summary


SECTION_LABELS = {
    "plain_english_summary": [
        "plain english summary",
        "plain-language summary",
        "plain language summary",
    ],
    "academic_summary": [
        "academic summary",
    ],
    "key_methods": [
        "key methods",
        "methods",
    ],
    "key_results": [
        "key results",
        "results",
        "key findings",
        "findings",
    ],
    "limitations": [
        "limitations",
    ],
    "practical_applications": [
        "practical applications",
        "applications",
        "practical use",
        "practical uses",
    ],
    "suggested_topics": [
        "suggested research topics",
        "suggested topics",
        "research topics",
        "recommended topics",
    ],
    "citation_guidance": [
        "citation guidance",
        "how to cite",
        "citation notes",
    ],
}


def parse_llm_sections(raw_text: str) -> dict:
    """
    Parse a structured LLM response into named sections.
    Works best when the model returns headings like:
    Plain English Summary:
    Academic Summary:
    Key Methods:
    ...
    """
    if not raw_text:
        return {
            "plain_english_summary": "",
            "academic_summary": "",
            "key_methods": "",
            "key_results": "",
            "limitations": "",
            "practical_applications": "",
            "suggested_topics": "",
            "citation_guidance": "",
            "raw_llm_summary": "",
        }

    text = raw_text.replace("\r", "").strip()

    normalized_patterns = []
    for canonical_name, label_list in SECTION_LABELS.items():
        for label in label_list:
            normalized_patterns.append((canonical_name, label))

    # Create a regex that matches any heading at the beginning of a line,
    # optionally preceded by numbering like "1." or "2)"
    pattern = re.compile(
        r"(?im)^\s*(?:\d+[\.\)]\s*)?("
        + "|".join(re.escape(label) for _, label in normalized_patterns)
        + r")\s*:\s*"
    )

    matches = list(pattern.finditer(text))

    sections = {
        "plain_english_summary": "",
        "academic_summary": "",
        "key_methods": "",
        "key_results": "",
        "limitations": "",
        "practical_applications": "",
        "suggested_topics": "",
        "citation_guidance": "",
        "raw_llm_summary": text,
    }

    if not matches:
        sections["plain_english_summary"] = text[:1200]
        return sections

    # Helper to map matched label back to canonical field
    label_to_canonical = {}
    for canonical_name, label_list in SECTION_LABELS.items():
        for label in label_list:
            label_to_canonical[label.lower()] = canonical_name

    for i, match in enumerate(matches):
        label = match.group(1).strip().lower()
        canonical_name = label_to_canonical.get(label)
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        value = " ".join(text[start:end].strip().split())

        if canonical_name and value:
            if sections[canonical_name]:
                sections[canonical_name] += " " + value
            else:
                sections[canonical_name] = value

    return sections


def build_section_extract_rows(document_id: str, title: str, section_map: dict) -> list[dict]:
    section_rows = []

    mapping = {
        "abstract": section_map.get("abstract_summary", ""),
        "methods": section_map.get("methods_summary", ""),
        "results": section_map.get("results_summary", ""),
        "limitations": section_map.get("limitations_summary", ""),
        "conclusion": section_map.get("conclusion_summary", ""),
        "plain_english_summary": section_map.get("plain_english_summary", ""),
        "academic_summary": section_map.get("academic_summary", ""),
        "practical_applications": section_map.get("practical_applications", ""),
        "citation_guidance": section_map.get("citation_guidance", ""),
        "suggested_topics": section_map.get("suggested_topics", ""),
    }

    for section_name, section_text in mapping.items():
        section_text = section_text if isinstance(section_text, str) else ""
        section_rows.append({
            "document_id": document_id,
            "title": title,
            "section_name": section_name,
            "section_text": section_text,
            "section_char_count": len(section_text),
        })

    return section_rows


def main():
    registry = pd.read_csv(PROCESSED_DIR / "document_registry.csv")
    chunks = pd.read_csv(PROCESSED_DIR / "document_chunks.csv")

    summaries = []
    section_extracts = []

    for _, row in registry.iterrows():
        document_id = row["document_id"]
        title = row["title"]
        file_name = row["file_name"]

        doc_chunks = (
            chunks.loc[chunks["document_id"] == document_id]
            .sort_values("chunk_order")
            .copy()
        )

        full_text = " ".join(doc_chunks["chunk_text"].astype(str).tolist()).strip()

        # Heuristic summaries (fallback + structured extraction)
        heuristic_executive = summarize_text(full_text, mode="executive")
        heuristic_technical = summarize_text(full_text, mode="technical")

        # Local LLM summary
        try:
            raw_llm_summary = generate_paper_summary(full_text)
        except Exception as e:
            raw_llm_summary = f"LLM summary failed: {e}"

        llm_sections = parse_llm_sections(raw_llm_summary)

        # Final merged outputs:
        # Prefer LLM sections when present, fall back to heuristic extraction
        plain_english_summary = llm_sections.get("plain_english_summary", "") or heuristic_executive.get("summary", "")
        academic_summary = llm_sections.get("academic_summary", "") or heuristic_technical.get("summary", "")
        methods_summary = llm_sections.get("key_methods", "") or heuristic_technical.get("methods", "")
        results_summary = llm_sections.get("key_results", "") or heuristic_technical.get("results", "")
        limitations_summary = llm_sections.get("limitations", "") or heuristic_technical.get("limitations", "")
        practical_applications = llm_sections.get("practical_applications", "")
        suggested_topics = llm_sections.get("suggested_topics", "")
        citation_guidance = llm_sections.get("citation_guidance", "")
        abstract_summary = heuristic_executive.get("abstract", "")[:1200]
        conclusion_summary = heuristic_executive.get("conclusion", "")[:1200]

        summary_row = {
            "document_id": document_id,
            "title": title,
            "file_name": file_name,
            "executive_summary": plain_english_summary[:3000],
            "technical_summary": academic_summary[:3000],
            "abstract_summary": abstract_summary[:2000],
            "methods_summary": methods_summary[:2000],
            "results_summary": results_summary[:2000],
            "limitations_summary": limitations_summary[:2000],
            "conclusion_summary": conclusion_summary[:2000],
            "plain_english_summary": plain_english_summary[:3000],
            "academic_summary": academic_summary[:3000],
            "practical_applications": practical_applications[:2000],
            "suggested_topics": suggested_topics[:1200],
            "citation_guidance": citation_guidance[:1500],
            "raw_llm_summary": llm_sections.get("raw_llm_summary", "")[:10000],
        }
        summaries.append(summary_row)

        section_extracts.extend(build_section_extract_rows(document_id, title, summary_row))

    summaries_df = pd.DataFrame(summaries)
    sections_df = pd.DataFrame(section_extracts)

    summaries_path = PROCESSED_DIR / "document_summaries.csv"
    sections_path = PROCESSED_DIR / "document_section_extracts.csv"

    summaries_df.to_csv(summaries_path, index=False)
    sections_df.to_csv(sections_path, index=False)

    print("Document summarization complete.\n")
    print("Saved outputs:")
    print("-", summaries_path)
    print("-", sections_path)

    print("\nDocument summaries preview:")
    print(
        summaries_df[
            [
                "document_id",
                "title",
                "executive_summary",
                "technical_summary",
                "practical_applications",
                "suggested_topics",
            ]
        ].head()
    )

    print("\nSection extracts preview:")
    print(sections_df.head(15))


if __name__ == "__main__":
    main()
