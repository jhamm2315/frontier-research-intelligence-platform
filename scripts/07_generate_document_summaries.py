from pathlib import Path
import sys
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from config.settings import PROCESSED_DIR
from app.services.summarization_service import summarize_text


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
        )

        full_text = " ".join(doc_chunks["chunk_text"].astype(str).tolist()).strip()

        executive = summarize_text(full_text, mode="executive")
        technical = summarize_text(full_text, mode="technical")

        summaries.append({
            "document_id": document_id,
            "title": title,
            "file_name": file_name,
            "executive_summary": executive["summary"],
            "technical_summary": technical["summary"],
            "abstract_summary": executive["abstract"][:500],
            "methods_summary": technical["methods"][:500],
            "results_summary": technical["results"][:500],
            "limitations_summary": technical["limitations"][:500],
            "conclusion_summary": executive["conclusion"][:500],
        })

        for section_name in ["abstract", "methods", "results", "limitations", "conclusion"]:
            section_extracts.append({
                "document_id": document_id,
                "title": title,
                "section_name": section_name,
                "section_text": technical.get(section_name, ""),
                "section_char_count": len(technical.get(section_name, "")),
            })

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
    print(summaries_df.head())

    print("\nSection extracts preview:")
    print(sections_df.head(15))


if __name__ == "__main__":
    main()
