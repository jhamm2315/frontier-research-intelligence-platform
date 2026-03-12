from pathlib import Path
import sys
import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from config.settings import PROCESSED_DIR


CURRENT_YEAR = 2026


def normalize_work_score(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    # recency boost
    out["recency_boost"] = np.where(
        out["publication_year"] >= CURRENT_YEAR - 3, 1.25,
        np.where(out["publication_year"] >= CURRENT_YEAR - 6, 1.10, 0.85)
    )

    # dampen old citation totals with log scaling
    out["log_citations"] = np.log1p(out["cited_by_count"])

    # more balanced breakthrough score
    out["breakthrough_rank_score"] = (
        out["citation_velocity"] * 0.45
        + out["log_citations"] * 0.25
        + out["primary_topic_score"].fillna(0) * 0.15
        + out["recency_boost"] * 0.15
    ).round(4)

    return out


def normalize_author_score(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    out["recency_factor"] = np.where(
        out["last_publication_year"] >= CURRENT_YEAR - 2, 1.20,
        np.where(out["last_publication_year"] >= CURRENT_YEAR - 5, 1.05, 0.85)
    )

    out["papers_log"] = np.log1p(out["papers_count"])
    out["citations_log"] = np.log1p(out["total_citations"])

    out["rising_author_score"] = (
        out["citation_velocity"] * 0.40
        + out["avg_citations"] * 0.20
        + out["papers_log"] * 0.15
        + out["citations_log"] * 0.10
        + out["recency_factor"] * 0.15
    ).round(4)

    return out


def normalize_institution_score(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    out["recency_factor"] = np.where(
        out["last_publication_year"] >= CURRENT_YEAR - 2, 1.20,
        np.where(out["last_publication_year"] >= CURRENT_YEAR - 5, 1.05, 0.85)
    )

    out["papers_log"] = np.log1p(out["papers_count"])
    out["authors_log"] = np.log1p(out["distinct_authors"])
    out["citations_log"] = np.log1p(out["total_citations"])

    out["rising_institution_score"] = (
        out["citation_velocity"] * 0.35
        + out["avg_citations"] * 0.20
        + out["authors_log"] * 0.20
        + out["papers_log"] * 0.10
        + out["recency_factor"] * 0.15
    ).round(4)

    return out


def normalize_topic_score(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    out["recency_factor"] = np.where(
        out["last_publication_year"] >= CURRENT_YEAR - 2, 1.25,
        np.where(out["last_publication_year"] >= CURRENT_YEAR - 5, 1.10, 0.85)
    )

    out["works_log"] = np.log1p(out["works_count"])
    out["citations_log"] = np.log1p(out["total_citations"])

    out["emerging_topic_score"] = (
        out["citation_velocity"] * 0.35
        + out["avg_topic_score"] * 0.20
        + out["avg_citations"] * 0.15
        + out["works_log"] * 0.10
        + out["recency_factor"] * 0.20
    ).round(4)

    return out


def main():
    works = pd.read_csv(PROCESSED_DIR / "works_clean.csv")
    authors = pd.read_csv(PROCESSED_DIR / "authors_extracted.csv")
    institutions = pd.read_csv(PROCESSED_DIR / "institutions_extracted.csv")
    topics = pd.read_csv(PROCESSED_DIR / "topics_extracted.csv")

    author_features = pd.read_csv(PROCESSED_DIR / "author_research_features.csv")
    institution_features = pd.read_csv(PROCESSED_DIR / "institution_research_features.csv")
    topic_features = pd.read_csv(PROCESSED_DIR / "topic_research_features.csv")
    summaries = pd.read_csv(PROCESSED_DIR / "document_summaries.csv")

    # --- works / breakthrough candidates
    works_ranked = normalize_work_score(works)

    # map summaries to sample docs using row order for now
    if len(summaries) == len(works_ranked.head(len(summaries))):
        works_ranked.loc[:len(summaries)-1, "executive_summary"] = summaries["executive_summary"].values
        works_ranked.loc[:len(summaries)-1, "technical_summary"] = summaries["technical_summary"].values
    else:
        works_ranked["executive_summary"] = ""
        works_ranked["technical_summary"] = ""

    top_breakthrough_candidates = (
        works_ranked[
            [
                "work_id",
                "title",
                "publication_year",
                "primary_topic",
                "cited_by_count",
                "citation_velocity",
                "breakthrough_rank_score",
                "executive_summary",
            ]
        ]
        .sort_values("breakthrough_rank_score", ascending=False)
        .head(25)
        .copy()
    )

    # --- topics
    topic_ranked = normalize_topic_score(topic_features).merge(
        topics[["topic_id", "topic_name"]].drop_duplicates(),
        on="topic_id",
        how="left"
    )

    top_emerging_topics = (
        topic_ranked[
            [
                "topic_id",
                "topic_name",
                "works_count",
                "total_citations",
                "avg_topic_score",
                "citation_velocity",
                "emerging_topic_score",
                "last_publication_year",
            ]
        ]
        .sort_values("emerging_topic_score", ascending=False)
        .head(25)
        .copy()
    )

    # --- authors
    author_ranked = normalize_author_score(author_features).merge(
        authors.drop_duplicates(),
        on="author_id",
        how="left"
    )

    top_rising_authors = (
        author_ranked[
            [
                "author_id",
                "author_name",
                "papers_count",
                "total_citations",
                "avg_citations",
                "citation_velocity",
                "rising_author_score",
                "last_publication_year",
            ]
        ]
        .sort_values("rising_author_score", ascending=False)
        .head(25)
        .copy()
    )

    # --- institutions
    institution_ranked = normalize_institution_score(institution_features).merge(
        institutions.drop_duplicates(),
        on="institution_id",
        how="left"
    )

    top_rising_institutions = (
        institution_ranked[
            [
                "institution_id",
                "institution_name",
                "country_code",
                "papers_count",
                "distinct_authors",
                "total_citations",
                "citation_velocity",
                "rising_institution_score",
                "last_publication_year",
            ]
        ]
        .sort_values("rising_institution_score", ascending=False)
        .head(25)
        .copy()
    )

    # --- summary table
    summary_df = pd.DataFrame([
        {
            "metric": "total_works",
            "value": len(works),
        },
        {
            "metric": "total_authors",
            "value": len(authors["author_id"].dropna().unique()),
        },
        {
            "metric": "total_institutions",
            "value": len(institutions["institution_id"].dropna().unique()),
        },
        {
            "metric": "total_topics",
            "value": len(topics["topic_id"].dropna().unique()),
        },
        {
            "metric": "top_breakthrough_title",
            "value": top_breakthrough_candidates.iloc[0]["title"] if not top_breakthrough_candidates.empty else "",
        },
        {
            "metric": "top_emerging_topic",
            "value": top_emerging_topics.iloc[0]["topic_name"] if not top_emerging_topics.empty else "",
        },
        {
            "metric": "top_rising_author",
            "value": top_rising_authors.iloc[0]["author_name"] if not top_rising_authors.empty else "",
        },
        {
            "metric": "top_rising_institution",
            "value": top_rising_institutions.iloc[0]["institution_name"] if not top_rising_institutions.empty else "",
        },
    ])

    # save outputs
    top_breakthrough_candidates.to_csv(PROCESSED_DIR / "top_breakthrough_candidates.csv", index=False)
    top_emerging_topics.to_csv(PROCESSED_DIR / "top_emerging_topics.csv", index=False)
    top_rising_authors.to_csv(PROCESSED_DIR / "top_rising_authors.csv", index=False)
    top_rising_institutions.to_csv(PROCESSED_DIR / "top_rising_institutions.csv", index=False)
    summary_df.to_csv(PROCESSED_DIR / "research_rankings_summary.csv", index=False)

    print("Research rankings generation complete.\n")
    print("Saved outputs:")
    print("-", PROCESSED_DIR / "top_breakthrough_candidates.csv")
    print("-", PROCESSED_DIR / "top_emerging_topics.csv")
    print("-", PROCESSED_DIR / "top_rising_authors.csv")
    print("-", PROCESSED_DIR / "top_rising_institutions.csv")
    print("-", PROCESSED_DIR / "research_rankings_summary.csv")

    print("\nTop breakthrough candidates:")
    print(top_breakthrough_candidates.head(10))

    print("\nTop emerging topics:")
    print(top_emerging_topics.head(10))

    print("\nTop rising authors:")
    print(top_rising_authors.head(10))

    print("\nTop rising institutions:")
    print(top_rising_institutions.head(10))


if __name__ == "__main__":
    main()
