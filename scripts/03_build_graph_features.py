from pathlib import Path
import sys
import json
import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from config.settings import PROCESSED_DIR, OPENALEX_WORKS_PATH


CURRENT_YEAR = 2026


def safe_load_json(value):
    if pd.isna(value):
        return []
    try:
        parsed = json.loads(value)
        return parsed if isinstance(parsed, list) else []
    except Exception:
        return []


def normalize_work_id(work_id: str) -> str:
    if pd.isna(work_id):
        return ""
    return str(work_id).replace("https://openalex.org/", "")


def extract_authors_and_institutions(df: pd.DataFrame):
    author_rows = []
    institution_rows = []
    work_author_edges = []
    work_institution_edges = []

    for _, row in df.iterrows():
        work_id = normalize_work_id(row["id"])
        cited_by_count = row.get("cited_by_count", 0)
        publication_year = row.get("publication_year", np.nan)

        authorships = safe_load_json(row.get("authorships"))

        for author_position, authorship in enumerate(authorships, start=1):
            author = authorship.get("author", {}) if isinstance(authorship, dict) else {}
            institutions = authorship.get("institutions", []) if isinstance(authorship, dict) else []

            author_id = str(author.get("id", "")).replace("https://openalex.org/", "")
            author_name = author.get("display_name")

            if author_id:
                author_rows.append({
                    "author_id": author_id,
                    "author_name": author_name,
                })

                work_author_edges.append({
                    "work_id": work_id,
                    "author_id": author_id,
                    "author_position": author_position,
                    "is_corresponding": authorship.get("is_corresponding"),
                    "publication_year": publication_year,
                    "cited_by_count": cited_by_count,
                })

            for inst in institutions if isinstance(institutions, list) else []:
                inst_id = str(inst.get("id", "")).replace("https://openalex.org/", "")
                inst_name = inst.get("display_name")
                country_code = inst.get("country_code")
                inst_type = inst.get("type")
                lineage = inst.get("lineage", [])

                if inst_id:
                    institution_rows.append({
                        "institution_id": inst_id,
                        "institution_name": inst_name,
                        "country_code": country_code,
                        "institution_type": inst_type,
                        "lineage_count": len(lineage) if isinstance(lineage, list) else 0,
                    })

                    work_institution_edges.append({
                        "work_id": work_id,
                        "institution_id": inst_id,
                        "author_id": author_id,
                        "publication_year": publication_year,
                        "cited_by_count": cited_by_count,
                    })

    authors_df = pd.DataFrame(author_rows).drop_duplicates()
    institutions_df = pd.DataFrame(institution_rows).drop_duplicates()
    work_author_edges_df = pd.DataFrame(work_author_edges)
    work_institution_edges_df = pd.DataFrame(work_institution_edges)

    return authors_df, institutions_df, work_author_edges_df, work_institution_edges_df


def extract_topics(df: pd.DataFrame):
    topic_rows = []
    work_topic_edges = []

    for _, row in df.iterrows():
        work_id = normalize_work_id(row["id"])
        publication_year = row.get("publication_year", np.nan)
        cited_by_count = row.get("cited_by_count", 0)

        concepts = safe_load_json(row.get("concepts"))

        for concept in concepts:
            concept_id = str(concept.get("id", "")).replace("https://openalex.org/", "")
            concept_name = concept.get("display_name")
            score = concept.get("score")
            level = concept.get("level")

            if concept_id:
                topic_rows.append({
                    "topic_id": concept_id,
                    "topic_name": concept_name,
                    "topic_level": level,
                })

                work_topic_edges.append({
                    "work_id": work_id,
                    "topic_id": concept_id,
                    "topic_score": score,
                    "publication_year": publication_year,
                    "cited_by_count": cited_by_count,
                })

    topics_df = pd.DataFrame(topic_rows).drop_duplicates()
    work_topic_edges_df = pd.DataFrame(work_topic_edges)

    return topics_df, work_topic_edges_df


def build_author_features(work_author_edges_df: pd.DataFrame):
    if work_author_edges_df.empty:
        return pd.DataFrame()

    df = work_author_edges_df.copy()
    df["paper_age"] = CURRENT_YEAR - df["publication_year"].fillna(CURRENT_YEAR)
    df["paper_age"] = df["paper_age"].clip(lower=1)

    author_features = (
        df.groupby("author_id", as_index=False)
        .agg(
            papers_count=("work_id", "count"),
            total_citations=("cited_by_count", "sum"),
            avg_citations=("cited_by_count", "mean"),
            first_publication_year=("publication_year", "min"),
            last_publication_year=("publication_year", "max"),
            median_author_position=("author_position", "median"),
        )
    )

    author_features["career_span_years"] = (
        author_features["last_publication_year"] - author_features["first_publication_year"] + 1
    ).clip(lower=1)

    author_features["citation_velocity"] = (
        author_features["total_citations"] / author_features["career_span_years"]
    ).round(2)

    author_features["author_momentum_score"] = (
        author_features["avg_citations"] * 0.5
        + author_features["citation_velocity"] * 0.3
        + author_features["papers_count"] * 0.2
    ).round(3)

    return author_features.sort_values("author_momentum_score", ascending=False)


def build_institution_features(work_institution_edges_df: pd.DataFrame):
    if work_institution_edges_df.empty:
        return pd.DataFrame()

    df = work_institution_edges_df.copy()

    institution_features = (
        df.groupby("institution_id", as_index=False)
        .agg(
            papers_count=("work_id", "nunique"),
            total_citations=("cited_by_count", "sum"),
            avg_citations=("cited_by_count", "mean"),
            first_publication_year=("publication_year", "min"),
            last_publication_year=("publication_year", "max"),
            distinct_authors=("author_id", "nunique"),
        )
    )

    institution_features["research_span_years"] = (
        institution_features["last_publication_year"] - institution_features["first_publication_year"] + 1
    ).clip(lower=1)

    institution_features["citation_velocity"] = (
        institution_features["total_citations"] / institution_features["research_span_years"]
    ).round(2)

    institution_features["institution_momentum_score"] = (
        institution_features["avg_citations"] * 0.5
        + institution_features["citation_velocity"] * 0.3
        + institution_features["distinct_authors"] * 0.2
    ).round(3)

    return institution_features.sort_values("institution_momentum_score", ascending=False)


def build_topic_features(work_topic_edges_df: pd.DataFrame):
    if work_topic_edges_df.empty:
        return pd.DataFrame()

    df = work_topic_edges_df.copy()

    topic_features = (
        df.groupby("topic_id", as_index=False)
        .agg(
            works_count=("work_id", "nunique"),
            total_citations=("cited_by_count", "sum"),
            avg_topic_score=("topic_score", "mean"),
            avg_citations=("cited_by_count", "mean"),
            first_publication_year=("publication_year", "min"),
            last_publication_year=("publication_year", "max"),
        )
    )

    topic_features["topic_span_years"] = (
        topic_features["last_publication_year"] - topic_features["first_publication_year"] + 1
    ).clip(lower=1)

    topic_features["citation_velocity"] = (
        topic_features["total_citations"] / topic_features["topic_span_years"]
    ).round(2)

    topic_features["topic_momentum_score"] = (
        topic_features["avg_citations"] * 0.4
        + topic_features["citation_velocity"] * 0.4
        + topic_features["works_count"] * 0.2
    ).round(3)

    return topic_features.sort_values("topic_momentum_score", ascending=False)


def main():
    df = pd.read_csv(OPENALEX_WORKS_PATH).copy()

    df["work_id"] = df["id"].apply(normalize_work_id)
    df["work_age"] = CURRENT_YEAR - df["publication_year"].fillna(CURRENT_YEAR)
    df["work_age"] = df["work_age"].clip(lower=1)

    df["citation_velocity"] = (df["cited_by_count"] / df["work_age"]).round(3)
    df["is_recent_work"] = np.where(df["publication_year"] >= CURRENT_YEAR - 3, 1, 0)
    df["breakthrough_proxy_score"] = (
        df["citation_velocity"] * 0.5
        + df["cited_by_count"] * 0.3
        + df["primary_topic_score"].fillna(0) * 0.2
    ).round(3)

    works_clean = df[[
        "work_id",
        "id",
        "doi",
        "title",
        "display_name",
        "publication_year",
        "publication_date",
        "type",
        "cited_by_count",
        "is_oa",
        "open_access_url",
        "primary_topic",
        "primary_topic_score",
        "institutions_distinct_count",
        "authors_count",
        "source_query",
        "work_age",
        "citation_velocity",
        "is_recent_work",
        "breakthrough_proxy_score",
    ]].copy()

    authors_df, institutions_df, work_author_edges_df, work_institution_edges_df = extract_authors_and_institutions(df)
    topics_df, work_topic_edges_df = extract_topics(df)

    author_features = build_author_features(work_author_edges_df)
    institution_features = build_institution_features(work_institution_edges_df)
    topic_features = build_topic_features(work_topic_edges_df)

    works_clean.to_csv(PROCESSED_DIR / "works_clean.csv", index=False)
    authors_df.to_csv(PROCESSED_DIR / "authors_extracted.csv", index=False)
    institutions_df.to_csv(PROCESSED_DIR / "institutions_extracted.csv", index=False)
    topics_df.to_csv(PROCESSED_DIR / "topics_extracted.csv", index=False)
    work_author_edges_df.to_csv(PROCESSED_DIR / "work_author_edges.csv", index=False)
    work_institution_edges_df.to_csv(PROCESSED_DIR / "work_institution_edges.csv", index=False)
    work_topic_edges_df.to_csv(PROCESSED_DIR / "work_topic_edges.csv", index=False)
    author_features.to_csv(PROCESSED_DIR / "author_research_features.csv", index=False)
    institution_features.to_csv(PROCESSED_DIR / "institution_research_features.csv", index=False)
    topic_features.to_csv(PROCESSED_DIR / "topic_research_features.csv", index=False)

    print("Graph feature build complete.\n")
    print("Saved outputs:")
    for name in [
        "works_clean.csv",
        "authors_extracted.csv",
        "institutions_extracted.csv",
        "topics_extracted.csv",
        "work_author_edges.csv",
        "work_institution_edges.csv",
        "work_topic_edges.csv",
        "author_research_features.csv",
        "institution_research_features.csv",
        "topic_research_features.csv",
    ]:
        print("-", PROCESSED_DIR / name)

    print("\nTop author features:")
    print(author_features.head(10))

    print("\nTop institution features:")
    print(institution_features.head(10))

    print("\nTop topic features:")
    print(topic_features.head(10))


if __name__ == "__main__":
    main()
