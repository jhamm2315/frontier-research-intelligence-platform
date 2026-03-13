from pathlib import Path
import sys
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from config.settings import PROCESSED_DIR


def normalize_title(value: str) -> str:
    if pd.isna(value):
        return ""
    return " ".join(str(value).lower().split())


def main():
    works_path = PROCESSED_DIR / "works_clean.csv"
    registry_path = PROCESSED_DIR / "document_registry.csv"
    summaries_path = PROCESSED_DIR / "document_summaries.csv"

    works = pd.read_csv(works_path).copy()
    registry = pd.read_csv(registry_path).copy()
    summaries = pd.read_csv(summaries_path).copy()

    works["title_norm"] = works["title"].apply(normalize_title)
    registry["title_norm"] = registry["title"].apply(normalize_title)

    catalog = works.merge(
        registry[
            [
                "document_id",
                "title",
                "author",
                "institution",
                "topic",
                "citation",
                "title_norm",
            ]
        ],
        on="title_norm",
        how="left",
        suffixes=("_work", "_doc"),
    )

    catalog = catalog.merge(
        summaries[
            [
                "document_id",
                "executive_summary",
                "technical_summary",
                "methods_summary",
                "results_summary",
                "limitations_summary",
                "conclusion_summary",
            ]
        ],
        on="document_id",
        how="left",
    )

    # Restore clean display fields after merge
    catalog["title"] = catalog["title_work"]
    catalog["document_title"] = catalog["title_doc"]

    catalog["has_full_document"] = catalog["document_id"].notna().astype(int)
    catalog["display_topic"] = catalog["topic"].fillna(catalog["primary_topic"])
    catalog["display_author"] = catalog["author"].fillna("Unknown")
    catalog["display_institution"] = catalog["institution"].fillna("Unknown")
    catalog["display_citation"] = catalog["citation"].fillna("")
    catalog["availability_label"] = catalog["has_full_document"].map(
        {1: "Full Document Available", 0: "Metadata Only"}
    )

    out = catalog[
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
            "executive_summary",
            "technical_summary",
            "methods_summary",
            "results_summary",
            "limitations_summary",
            "conclusion_summary",
        ]
    ].copy()

    out = out.sort_values(
        ["has_full_document", "breakthrough_proxy_score", "cited_by_count"],
        ascending=[False, False, False]
    ).reset_index(drop=True)

    out_path = PROCESSED_DIR / "paper_catalog.csv"
    out.to_csv(out_path, index=False)

    print("Paper catalog build complete.")
    print(f"Saved to: {out_path}")
    print(f"Shape: {out.shape}")
    print("\nPreview:")
    print(out.head(15))


if __name__ == "__main__":
    main()
