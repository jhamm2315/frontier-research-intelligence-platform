from pathlib import Path
import sys
import pandas as pd
import json

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from config.settings import (
    OPENALEX_WORKS_PATH,
    PROFILE_OUTPUT_PATH,
    SCHEMA_REPORT_PATH,
    EXPECTED_WORK_COLUMNS,
)


def profile_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    profile = pd.DataFrame({
        "column": df.columns,
        "dtype": df.dtypes.astype(str).values,
        "null_count": df.isna().sum().values,
        "null_pct": (df.isna().mean() * 100).round(2).values,
        "distinct_count": df.nunique(dropna=False).values,
    })
    return profile


def count_concepts(concepts_str: str) -> int:
    if pd.isna(concepts_str):
        return 0
    try:
        concepts = json.loads(concepts_str)
        return len(concepts) if isinstance(concepts, list) else 0
    except Exception:
        return 0


def count_authorships(authorships_str: str) -> int:
    if pd.isna(authorships_str):
        return 0
    try:
        authorships = json.loads(authorships_str)
        return len(authorships) if isinstance(authorships, list) else 0
    except Exception:
        return 0


def main():
    df = pd.read_csv(OPENALEX_WORKS_PATH)

    actual_columns = list(df.columns)
    missing_columns = sorted(list(set(EXPECTED_WORK_COLUMNS) - set(actual_columns)))
    unexpected_columns = sorted(list(set(actual_columns) - set(EXPECTED_WORK_COLUMNS)))

    schema_report = pd.DataFrame([{
        "row_count": len(df),
        "column_count": len(df.columns),
        "missing_columns": ", ".join(missing_columns) if missing_columns else "",
        "unexpected_columns": ", ".join(unexpected_columns) if unexpected_columns else "",
        "schema_valid": len(missing_columns) == 0,
    }])

    profile_df = profile_dataframe(df)

    duplicate_report = pd.DataFrame([{
        "duplicate_rows": int(df.duplicated().sum()),
        "duplicate_ids": int(df["id"].duplicated().sum()) if "id" in df.columns else None,
        "duplicate_dois": int(df["doi"].duplicated().sum()) if "doi" in df.columns else None,
    }])

    publication_summary = pd.DataFrame([{
        "min_publication_year": int(df["publication_year"].min()) if "publication_year" in df.columns and df["publication_year"].notna().any() else None,
        "max_publication_year": int(df["publication_year"].max()) if "publication_year" in df.columns and df["publication_year"].notna().any() else None,
        "avg_cited_by_count": round(float(df["cited_by_count"].mean()), 2) if "cited_by_count" in df.columns else None,
        "max_cited_by_count": int(df["cited_by_count"].max()) if "cited_by_count" in df.columns and df["cited_by_count"].notna().any() else None,
    }])

    topic_distribution = (
        df["primary_topic"]
        .fillna("Unknown")
        .value_counts()
        .rename_axis("primary_topic")
        .reset_index(name="count")
    )

    derived_quality = pd.DataFrame({
        "id": df["id"],
        "title": df["title"],
        "publication_year": df["publication_year"],
        "cited_by_count": df["cited_by_count"],
        "concept_count": df["concepts"].apply(count_concepts),
        "authors_count_derived": df["authorships"].apply(count_authorships),
        "primary_topic": df["primary_topic"],
        "source_query": df["source_query"],
    })

    schema_report.to_csv(SCHEMA_REPORT_PATH, index=False)

    with pd.ExcelWriter(PROFILE_OUTPUT_PATH, engine="openpyxl") as writer:
        profile_df.to_excel(writer, sheet_name="profile", index=False)
        schema_report.to_excel(writer, sheet_name="schema_report", index=False)
        duplicate_report.to_excel(writer, sheet_name="duplicates", index=False)
        publication_summary.to_excel(writer, sheet_name="publication_summary", index=False)
        topic_distribution.to_excel(writer, sheet_name="topic_distribution", index=False)
        derived_quality.to_excel(writer, sheet_name="derived_quality", index=False)

    print("Validation and profiling complete.")
    print(f"Schema report saved to: {SCHEMA_REPORT_PATH}")
    print(f"Profile workbook saved to: {PROFILE_OUTPUT_PATH}")
    print("\nSchema report:")
    print(schema_report)
    print("\nDuplicate report:")
    print(duplicate_report)
    print("\nPublication summary:")
    print(publication_summary)
    print("\nTop topics:")
    print(topic_distribution.head(10))


if __name__ == "__main__":
    main()
