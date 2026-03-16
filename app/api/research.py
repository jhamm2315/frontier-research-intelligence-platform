from pathlib import Path
import pandas as pd
import numpy as np
from fastapi import APIRouter, Query
from fastapi.encoders import jsonable_encoder

from app.services.source_connector_service import (
    search_arxiv,
    fetch_arxiv_by_id,
    build_text_document_from_arxiv,
)
from app.services.pipeline_refresh_service import refresh_document_pipeline

router = APIRouter()

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
CATALOG_PATH = PROCESSED_DIR / "paper_catalog.csv"
SUMMARY_PATH = PROCESSED_DIR / "document_summaries.csv"


def load_catalog() -> pd.DataFrame:
    if not CATALOG_PATH.exists():
        return pd.DataFrame()
    return pd.read_csv(CATALOG_PATH)


def load_summaries() -> pd.DataFrame:
    if not SUMMARY_PATH.exists():
        return pd.DataFrame()
    return pd.read_csv(SUMMARY_PATH)


def clean_for_json_df(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df = df.replace([np.inf, -np.inf], np.nan)
    df = df.astype(object)
    df = df.where(pd.notnull(df), None)
    return df


def clean_for_json_dict(d: dict) -> dict:
    cleaned = {}
    for k, v in d.items():
        if isinstance(v, float) and (np.isnan(v) or np.isinf(v)):
            cleaned[k] = None
        elif pd.isna(v) if not isinstance(v, (list, dict, str, bool, int)) else False:
            cleaned[k] = None
        else:
            cleaned[k] = v
    return cleaned


@router.get("/health")
def research_health():
    return {"status": "research api ok"}


@router.get("/catalog")
def get_catalog(limit: int = 50):
    df = load_catalog()
    if df.empty:
        return []

    df = clean_for_json_df(df.head(limit))
    return jsonable_encoder(df.to_dict(orient="records"))


@router.get("/search")
def search_catalog(
    q: str = Query(..., description="Search papers by title, topic, author, or institution"),
    limit: int = 25
):
    df = load_catalog()
    if df.empty:
        return []

    query = q.strip().lower()

    mask = (
        df["title"].fillna("").astype(str).str.lower().str.contains(query, na=False)
        | df["display_topic"].fillna("").astype(str).str.lower().str.contains(query, na=False)
        | df["primary_topic"].fillna("").astype(str).str.lower().str.contains(query, na=False)
        | df["display_author"].fillna("").astype(str).str.lower().str.contains(query, na=False)
        | df["display_institution"].fillna("").astype(str).str.lower().str.contains(query, na=False)
    )

    results = df.loc[mask].head(limit)
    results = clean_for_json_df(results)
    return jsonable_encoder(results.to_dict(orient="records"))


@router.get("/paper/{work_id}")
def get_paper_detail(work_id: str):
    catalog = load_catalog()
    summaries = load_summaries()

    if catalog.empty:
        return {"message": "Catalog not available."}

    row = catalog.loc[catalog["work_id"] == work_id]
    if row.empty:
        return {"message": f"Paper {work_id} not found."}

    row_dict = clean_for_json_dict(row.iloc[0].to_dict())
    document_id = row_dict.get("document_id")

    ai_summary = None
    if document_id and not summaries.empty:
        s = summaries.loc[summaries["document_id"] == document_id]
        if not s.empty:
            ai_summary = clean_for_json_dict(s.iloc[0].to_dict())

    response = {
        "metadata": clean_for_json_dict({
            "work_id": row_dict.get("work_id"),
            "document_id": row_dict.get("document_id"),
            "title": row_dict.get("title"),
            "author": row_dict.get("display_author"),
            "institution": row_dict.get("display_institution"),
            "topic": row_dict.get("display_topic"),
            "primary_topic": row_dict.get("primary_topic"),
            "citation": row_dict.get("display_citation"),
            "publication_year": row_dict.get("publication_year"),
            "cited_by_count": row_dict.get("cited_by_count"),
            "source_system": row_dict.get("source_system"),
            "source_paper_id": row_dict.get("source_paper_id"),
            "published": row_dict.get("published"),
            "updated": row_dict.get("updated"),
            "pdf_url": row_dict.get("pdf_url"),
            "entry_url": row_dict.get("entry_url"),
            "categories": row_dict.get("categories"),
            "availability_label": row_dict.get("availability_label"),
            "has_full_document": row_dict.get("has_full_document"),
        }),
        "ai_summary": ai_summary,
    }

    return jsonable_encoder(response)


@router.get("/arxiv-search")
def arxiv_search(
    q: str = Query(..., description="Search arXiv by keyword"),
    limit: int = 10
):
    results = search_arxiv(q, max_results=limit)
    return jsonable_encoder(results)


@router.post("/arxiv-ingest")
def arxiv_ingest(arxiv_id: str = Query(..., description="arXiv identifier")):
    record = fetch_arxiv_by_id(arxiv_id)
    if not record:
        return {"success": False, "message": f"arXiv record {arxiv_id} not found."}

    stored_path = build_text_document_from_arxiv(record)
    refresh_result = refresh_document_pipeline()

    return {
        "success": refresh_result["success"],
        "message": "arXiv document ingested and pipeline refreshed." if refresh_result["success"] else refresh_result["message"],
        "arxiv_id": record.get("arxiv_id"),
        "title": record.get("title"),
        "authors": record.get("authors", []),
        "primary_category": record.get("primary_category"),
        "stored_path": str(stored_path),
        "pipeline": refresh_result,
    }
