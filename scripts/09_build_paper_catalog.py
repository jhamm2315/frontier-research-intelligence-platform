from pathlib import Path
import sys
import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from config.settings import PROCESSED_DIR


def normalize_title(value: str) -> str:
    if pd.isna(value):
        return ""
    return " ".join(str(value).lower().split())


def safe_year_from_text(value):
    if pd.isna(value) or not value:
        return np.nan
    try:
        return int(str(value)[:4])
    except Exception:
        return np.nan


def main():
    works = pd.read_csv(PROCESSED_DIR / "works_clean.csv").copy()
    registry = pd.read_csv(PROCESSED_DIR / "document_registry.csv").copy()
    summaries = pd.read_csv(PROCESSED_DIR / "document_summaries.csv").copy()

    works["title_norm"] = works["title"].apply(normalize_title)
    registry["title_norm"] = registry["title"].apply(normalize_title)

    # Match works to ingested docs by normalized title
    catalog = works.merge(
        registry[
            [
                "document_id",
                "title",
                "author",
                "institution",
                "topic",
                "citation",
                "source_system",
                "source_paper_id",
                "published",
                "updated",
                "pdf_url",
                "entry_url",
                "categories",
                "title_norm",
            ]
        ],
        on="title_norm",
        how="left",
        suffixes=("_work", "_doc"),
    )

    catalog = catalog.merge(
        summaries,
        on="document_id",
        how="left",
        suffixes=("", "_summary"),
    )

    # Restore clean title field for matched works
    if "title_work" in catalog.columns:
        catalog["title"] = catalog["title_work"]
    elif "title" not in catalog.columns:
        catalog["title"] = np.nan

    catalog["has_full_document"] = catalog["document_id"].notna().astype(int)
    catalog["display_topic"] = catalog["topic"].fillna(catalog["primary_topic"])
    catalog["display_author"] = catalog["author"].fillna("Unknown")
    catalog["display_institution"] = catalog["institution"].fillna("Unknown")
    catalog["display_citation"] = catalog["citation"].fillna("")
    catalog["availability_label"] = catalog["has_full_document"].map(
        {1: "Full Document Available", 0: "Metadata Only"}
    )

    works_catalog = catalog[
        [
            "work_id",
            "title",
            "publication_year",
            "primary_topic",
            "display_topic",
            "cited_by_count",
            "citation_velocity",
            "breakthrough_proxy_score",
            "document_id",
            "has_full_document",
            "availability_label",
            "display_author",
            "display_institution",
            "display_citation",
            "source_system",
            "source_paper_id",
            "published",
            "updated",
            "pdf_url",
            "entry_url",
            "categories",
            "plain_english_summary",
            "academic_summary",
            "executive_summary",
            "technical_summary",
            "methods_summary",
            "results_summary",
            "limitations_summary",
            "conclusion_summary",
            "practical_applications",
            "suggested_topics",
            "citation_guidance",
        ]
    ].copy()

    # Add ingested documents that do not match any OpenAlex work
    matched_doc_ids = set(works_catalog["document_id"].dropna().astype(str).unique())

    doc_only = registry.loc[
        ~registry["document_id"].astype(str).isin(matched_doc_ids)
    ].copy()

    doc_only = doc_only.merge(
        summaries,
        on="document_id",
        how="left",
        suffixes=("_reg", "_sum"),
    )

    if not doc_only.empty:
        # Normalize title after merge
        if "title_reg" in doc_only.columns:
            doc_only["title"] = doc_only["title_reg"]
        elif "title" not in doc_only.columns and "title_sum" in doc_only.columns:
            doc_only["title"] = doc_only["title_sum"]

        doc_only["work_id"] = "DOCWORK_" + doc_only["document_id"].astype(str)
        doc_only["publication_year"] = doc_only["published"].apply(safe_year_from_text)
        doc_only["primary_topic"] = doc_only["topic"]
        doc_only["display_topic"] = doc_only["topic"].fillna("Unknown")
        doc_only["cited_by_count"] = 0
        doc_only["citation_velocity"] = 0.0
        doc_only["breakthrough_proxy_score"] = 0.0
        doc_only["has_full_document"] = 1
        doc_only["availability_label"] = "Full Document Available"
        doc_only["display_author"] = doc_only["author"].fillna("Unknown")
        doc_only["display_institution"] = doc_only["institution"].fillna("Unknown")
        doc_only["display_citation"] = doc_only["citation"].fillna("")

        doc_only = doc_only[
            [
                "work_id",
                "title",
                "publication_year",
                "primary_topic",
                "display_topic",
                "cited_by_count",
                "citation_velocity",
                "breakthrough_proxy_score",
                "document_id",
                "has_full_document",
                "availability_label",
                "display_author",
                "display_institution",
                "display_citation",
                "source_system",
                "source_paper_id",
                "published",
                "updated",
                "pdf_url",
                "entry_url",
                "categories",
                "plain_english_summary",
                "academic_summary",
                "executive_summary",
                "technical_summary",
                "methods_summary",
                "results_summary",
                "limitations_summary",
                "conclusion_summary",
                "practical_applications",
                "suggested_topics",
                "citation_guidance",
            ]
        ].copy()

        final_catalog = pd.concat([works_catalog, doc_only], ignore_index=True)
    else:
        final_catalog = works_catalog.copy()

    final_catalog = final_catalog.sort_values(
        ["has_full_document", "breakthrough_proxy_score", "cited_by_count"],
        ascending=[False, False, False]
    ).reset_index(drop=True)

    out_path = PROCESSED_DIR / "paper_catalog.csv"
    final_catalog.to_csv(out_path, index=False)

    print("Paper catalog build complete.")
    print(f"Saved to: {out_path}")
    print(f"Shape: {final_catalog.shape}")
    print("\nAvailability counts:")
    print(final_catalog["availability_label"].value_counts(dropna=False))
    print("\nPreview:")
    print(final_catalog.head(15))


if __name__ == "__main__":
    main()
