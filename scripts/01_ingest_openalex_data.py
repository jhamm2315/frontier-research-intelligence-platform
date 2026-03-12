from pathlib import Path
import sys
import json
import time
import requests
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from config.settings import (
    OPENALEX_EMAIL,
    OPENALEX_BASE_URL,
    OPENALEX_SAMPLE_TOPICS,
    OPENALEX_PER_TOPIC,
    OPENALEX_WORKS_PATH,
)


def extract_primary_topic(work: dict) -> str | None:
    primary = work.get("primary_topic")
    if isinstance(primary, dict):
        return primary.get("display_name")
    return None


def extract_primary_topic_score(work: dict):
    primary = work.get("primary_topic")
    if isinstance(primary, dict):
        return primary.get("score")
    return None


def extract_open_access_url(work: dict) -> str | None:
    oa = work.get("open_access")
    if isinstance(oa, dict):
        return oa.get("oa_url")
    return None


def extract_authors_count(work: dict) -> int:
    authorships = work.get("authorships", [])
    return len(authorships) if isinstance(authorships, list) else 0


def flatten_work(work: dict, topic_query: str) -> dict:
    return {
        "id": work.get("id"),
        "doi": work.get("doi"),
        "title": work.get("title"),
        "display_name": work.get("display_name"),
        "publication_year": work.get("publication_year"),
        "publication_date": work.get("publication_date"),
        "type": work.get("type"),
        "cited_by_count": work.get("cited_by_count"),
        "cited_by_api_url": work.get("cited_by_api_url"),
        "is_oa": work.get("open_access", {}).get("is_oa") if isinstance(work.get("open_access"), dict) else None,
        "open_access_url": extract_open_access_url(work),
        "primary_topic": extract_primary_topic(work),
        "primary_topic_score": extract_primary_topic_score(work),
        "institutions_distinct_count": work.get("institutions_distinct_count"),
        "authors_count": extract_authors_count(work),
        "concepts": json.dumps(work.get("concepts", [])),
        "authorships": json.dumps(work.get("authorships", [])),
        "source_query": topic_query,
    }


def fetch_topic_works(topic_query: str, per_page: int = 40) -> list[dict]:
    params = {
        "search": topic_query,
        "per-page": per_page,
        "sort": "cited_by_count:desc",
    }

    if OPENALEX_EMAIL:
        params["mailto"] = OPENALEX_EMAIL

    response = requests.get(OPENALEX_BASE_URL, params=params, timeout=60)
    response.raise_for_status()

    payload = response.json()
    results = payload.get("results", [])

    records = [flatten_work(work, topic_query) for work in results]
    return records


def main():
    all_records = []

    for topic in OPENALEX_SAMPLE_TOPICS:
        print(f"Fetching works for topic: {topic}")
        records = fetch_topic_works(topic, per_page=OPENALEX_PER_TOPIC)
        all_records.extend(records)
        time.sleep(1)

    df = pd.DataFrame(all_records)

    # deduplicate by OpenAlex work ID
    if "id" in df.columns:
        df = df.drop_duplicates(subset=["id"]).reset_index(drop=True)

    df.to_csv(OPENALEX_WORKS_PATH, index=False)

    print("\nOpenAlex ingestion complete.")
    print(f"Saved to: {OPENALEX_WORKS_PATH}")
    print(f"Shape: {df.shape}")
    print("\nColumns:")
    print(df.columns.tolist())
    print("\nPreview:")
    print(df.head())


if __name__ == "__main__":
    main()
