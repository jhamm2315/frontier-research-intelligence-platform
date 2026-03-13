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


def load_catalog() -> pd.DataFrame:
    if not CATALOG_PATH.exists():
        return pd.DataFrame()
    return pd.read_csv(CATALOG_PATH)


def clean_for_json(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df = df.replace([np.inf, -np.inf], np.nan)
    df = df.astype(object)
    df = df.where(pd.notnull(df), None)
    return df


@router.get("/health")
def research_health():
    return {"status": "research api ok"}


@router.get("/catalog")
def get_catalog(limit: int = 50):
    df = load_catalog()
    if df.empty:
        return []

    df = clean_for_json(df.head(limit))
    return jsonable_encoder(df.to_dict(orient="records"))


@router.get("/search")
def search_catalog(
    q: str = Query(..., description="Search papers by title or topic"),
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
    results = clean_for_json(results)
    return jsonable_encoder(results.to_dict(orient="records"))


@router.get("/paper/{work_id}")
def get_paper_detail(work_id: str):
    df = load_catalog()
    if df.empty:
        return {"message": "Catalog not available."}

    row = df.loc[df["work_id"] == work_id]
    if row.empty:
        return {"message": f"Paper {work_id} not found."}

    row = clean_for_json(row)
    return jsonable_encoder(row.iloc[0].to_dict())


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
