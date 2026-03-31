from pathlib import Path
import pandas as pd
import numpy as np
from fastapi import APIRouter, HTTPException, Query
from fastapi.encoders import jsonable_encoder
from app.services.federated_search_service import federated_search
from pydantic import BaseModel
from app.services.multi_paper_service import compare_papers

from app.services.source_connector_service import (
    search_arxiv,
    fetch_arxiv_by_id,
    build_text_document_from_arxiv,
    build_fulltext_document_from_arxiv_pdf,
)
from app.services.open_access_ingestion_service import (
    get_featured_verified_open_access_sources,
    persist_verified_open_access_url,
    search_verified_open_access_records,
)
from app.services.open_access_index_service import (
    collect_open_access_index,
    list_open_access_ingestion_runs,
    search_indexed_open_access_sources,
)
from app.services.pipeline_refresh_service import refresh_document_pipeline
from app.services.usage_service import enforce_usage_limit, increment_usage
from app.services.recommendation_tracking_service import (
    safe_track_recommendation_activity_for_user,
)

class MultiPaperCompareRequest(BaseModel):
    work_ids: list[str]
    user_question: str | None = None
    user_id: str | None = None


class OpenAccessIngestRequest(BaseModel):
    url: str
    user_id: str | None = None
    mark_featured: bool = False


class OpenAccessBatchIndexRequest(BaseModel):
    query: str
    user_id: str | None = None
    pages: int = 3
    limit_per_source: int = 50
    mark_featured: bool = False
    source_targets: list[str] | None = None

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


def find_catalog_record_for_ingested_paper(arxiv_id: str, title: str) -> dict | None:
    catalog = load_catalog()
    if catalog.empty:
        return None

    # First try exact source paper id match
    if "source_paper_id" in catalog.columns:
        m = catalog.loc[catalog["source_paper_id"].fillna("").astype(str) == str(arxiv_id)]
        if not m.empty:
            return clean_for_json_dict(m.iloc[0].to_dict())

    # Then try exact title match
    m = catalog.loc[catalog["title"].fillna("").astype(str).str.strip() == str(title).strip()]
    if not m.empty:
        return clean_for_json_dict(m.iloc[0].to_dict())

    # Then try contains
    m = catalog.loc[catalog["title"].fillna("").astype(str).str.contains(str(title), case=False, na=False)]
    if not m.empty:
        return clean_for_json_dict(m.iloc[0].to_dict())

    return None

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
    limit: int = 25,
    user_id: str | None = Query(None, description="Optional active user identifier"),
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
    records = results.to_dict(orient="records")

    safe_track_recommendation_activity_for_user(
        user_id,
        "search",
        {
            "query": q,
            "search_query": q,
            "search_mode": "catalog",
            "result_count": len(records),
            "event_source": "research.search",
            "action_context": "catalog_search",
            "metadata": {
                "top_results": [
                    {
                        "work_id": row.get("work_id"),
                        "title": row.get("title"),
                        "topic": row.get("display_topic") or row.get("primary_topic"),
                        "source_system": row.get("source_system"),
                        "result_rank": index + 1,
                    }
                    for index, row in enumerate(records[:10])
                ]
            },
        },
    )

    return jsonable_encoder(records)


@router.get("/paper/{work_id}")
def get_paper_detail(work_id: str, user_id: str | None = Query(None, description="Optional active user identifier")):
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

    safe_track_recommendation_activity_for_user(
        user_id,
        "view",
        {
            **(response.get("metadata") or {}),
            "event_source": "research.paper_detail",
            "action_context": "paper_detail_view",
        },
    )

    return jsonable_encoder(response)

@router.post("/compare-papers")
def compare_papers_route(payload: MultiPaperCompareRequest):
    if not payload.work_ids or len(payload.work_ids) < 2:
        return {
            "error": "Please provide at least 2 paper work_ids for comparison."
        }

    result = compare_papers(payload.work_ids, payload.user_question or "")

    for paper in result.get("papers", []):
        safe_track_recommendation_activity_for_user(
            payload.user_id,
            "compare",
            {
                **paper,
                "event_source": "research.compare",
                "action_context": "multi_paper_compare",
                "metadata": {
                    "compared_work_ids": payload.work_ids,
                    "question": payload.user_question,
                },
            },
        )

    return result


@router.get("/arxiv-search")
def arxiv_search(
    q: str = Query(..., description="Search arXiv by keyword"),
    limit: int = Query(25, ge=1, le=100),
    user_id: str | None = Query(None, description="Optional active user identifier"),
):
    results = search_arxiv(q, max_results=limit)

    safe_track_recommendation_activity_for_user(
        user_id,
        "search",
        {
            "query": q,
            "search_query": q,
            "search_mode": "arxiv",
            "result_count": len(results),
            "event_source": "research.arxiv_search",
            "action_context": "arxiv_search",
            "metadata": {
                "top_results": [
                    {
                        "work_id": row.get("arxiv_id"),
                        "title": row.get("title"),
                        "topic": row.get("primary_category"),
                        "result_rank": index + 1,
                    }
                    for index, row in enumerate(results[:10])
                ]
            },
        },
    )

    return jsonable_encoder(results)


@router.post("/arxiv-ingest")
def arxiv_ingest(
    arxiv_id: str = Query(..., description="arXiv identifier"),
    mode: str = Query("full", description="full or abstract"),
    user_id: str = Query("demo_user", description="active user identifier"),
    plan: str = Query("free", description="active subscription plan"),
):
    mode = (mode or "full").strip().lower()
    if mode not in {"full", "abstract"}:
        raise HTTPException(status_code=400, detail="mode must be 'full' or 'abstract'")

    try:
        enforce_usage_limit(user_id, "arxiv_ingests", plan)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc

    record = fetch_arxiv_by_id(arxiv_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"arXiv record {arxiv_id} not found.")

    try:
        if mode == "abstract":
            stored_path = build_text_document_from_arxiv(record)
        else:
            stored_path = build_fulltext_document_from_arxiv_pdf(record)

        refresh_result = refresh_document_pipeline()
        if not refresh_result["success"]:
            raise HTTPException(status_code=500, detail=refresh_result["message"])

        matched_record = find_catalog_record_for_ingested_paper(
            arxiv_id=record.get("arxiv_id", ""),
            title=record.get("title", "")
        )
        increment_usage(user_id, "arxiv_ingests", 1)

        safe_track_recommendation_activity_for_user(
            user_id,
            "upload",
            {
                "work_id": matched_record.get("work_id") if matched_record else record.get("arxiv_id"),
                "document_id": matched_record.get("document_id") if matched_record else None,
                "title": record.get("title"),
                "author": ", ".join(record.get("authors", [])),
                "topic": record.get("primary_category"),
                "source_system": "arxiv",
                "search_query": arxiv_id,
                "event_source": "research.arxiv_ingest",
                "action_context": "arxiv_ingest",
                "metadata": {
                    "ingestion_mode": mode,
                    "authors": record.get("authors", []),
                    "matched_work_id": matched_record.get("work_id") if matched_record else None,
                },
            },
        )

        return jsonable_encoder({
            "success": True,
            "message": "arXiv document ingested and pipeline refreshed.",
            "arxiv_id": record.get("arxiv_id"),
            "title": record.get("title"),
            "authors": record.get("authors", []),
            "primary_category": record.get("primary_category"),
            "stored_path": str(stored_path),
            "ingestion_mode": mode,
            "matched_work_id": matched_record.get("work_id") if matched_record else None,
            "matched_document_id": matched_record.get("document_id") if matched_record else None,
            "pipeline": refresh_result,
        })
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"arXiv ingest failed: {exc}") from exc
@router.get("/federated-search")
def federated_source_search(
    q: str = Query(..., description="Search across Harvard, MIT, Stanford, and Harvard LibraryCloud"),
    limit_per_source: int = Query(25, ge=1, le=100),
    page: int = Query(1, ge=1, le=50),
    user_id: str | None = Query(None, description="Optional active user identifier"),
):
    results = federated_search(q, limit_per_source=limit_per_source, page=page)

    safe_track_recommendation_activity_for_user(
        user_id,
        "search",
        {
            "query": q,
            "search_query": q,
            "search_mode": "federated",
            "result_count": len(results),
            "event_source": "research.federated_search",
            "action_context": "federated_search",
            "metadata": {
                "top_results": [
                    {
                        "work_id": row.get("work_id") or row.get("source_paper_id"),
                        "title": row.get("title"),
                        "topic": row.get("primary_topic") or row.get("topic"),
                        "source_system": row.get("source_system"),
                        "result_rank": index + 1,
                    }
                    for index, row in enumerate(results[:10])
                ]
            },
        },
    )

    return jsonable_encoder(results)


@router.get("/open-access/search")
def open_access_search(
    q: str = Query(..., description="Search verified open-access scholarly sources"),
    limit_per_source: int = Query(25, ge=1, le=100),
    page: int = Query(1, ge=1, le=50),
    user_id: str | None = Query(None, description="Optional active user identifier"),
):
    results = search_verified_open_access_records(q, limit_per_source=limit_per_source, page=page)

    safe_track_recommendation_activity_for_user(
        user_id,
        "search",
        {
            "query": q,
            "search_query": q,
            "search_mode": "open_access",
            "result_count": len(results),
            "event_source": "research.open_access_search",
            "action_context": "open_access_search",
            "metadata": {
                "top_results": [
                    {
                        "work_id": row.get("source_key"),
                        "title": row.get("title"),
                        "topic": (row.get("topics") or [None])[0],
                        "source_system": row.get("source_system"),
                        "result_rank": index + 1,
                    }
                    for index, row in enumerate(results[:10])
                ]
            },
        },
    )

    return jsonable_encoder(results)


@router.post("/open-access/ingest-url")
def open_access_ingest_url(payload: OpenAccessIngestRequest):
    result = persist_verified_open_access_url(
        payload.url,
        requested_by_clerk_user_id=payload.user_id,
        mark_featured=payload.mark_featured,
    )
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("message") or "Open-access URL ingest failed.")

    source = result.get("source") or {}
    safe_track_recommendation_activity_for_user(
        payload.user_id,
        "upload",
        {
            "work_id": source.get("source_key"),
            "title": source.get("title"),
            "topic": (source.get("topics") or [None])[0],
            "source_system": source.get("source_system"),
            "search_query": payload.url,
            "event_source": "research.open_access_ingest_url",
            "action_context": "open_access_ingest_url",
            "metadata": {
                "canonical_url": source.get("canonical_url"),
                "pdf_url": source.get("pdf_url"),
                "featured": source.get("is_featured"),
            },
        },
    )

    return jsonable_encoder(result)


@router.get("/open-access/featured")
def featured_open_access_sources(limit: int = 12):
    return jsonable_encoder(get_featured_verified_open_access_sources(limit=limit))


@router.post("/open-access/index")
def batch_index_open_access(payload: OpenAccessBatchIndexRequest):
    try:
        result = collect_open_access_index(
            query=payload.query,
            pages=payload.pages,
            limit_per_source=payload.limit_per_source,
            requested_by_clerk_user_id=payload.user_id,
            mark_featured=payload.mark_featured,
            source_targets=tuple(payload.source_targets or ()),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Open-access batch index failed: {exc}") from exc

    safe_track_recommendation_activity_for_user(
        payload.user_id,
        "search",
        {
            "query": payload.query,
            "search_query": payload.query,
            "search_mode": "open_access_batch_index",
            "result_count": result.get("record_count", 0),
            "event_source": "research.open_access_index",
            "action_context": "open_access_batch_index",
            "metadata": {
                "pages": payload.pages,
                "limit_per_source": payload.limit_per_source,
                "warning_count": result.get("warning_count", 0),
            },
        },
    )
    return jsonable_encoder(result)


@router.get("/open-access/indexed")
def indexed_open_access_search(
    q: str = Query("", description="Search the stored open-access catalog"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0, le=5000),
    source_system: str | None = Query(None),
    summary_ready_only: bool = Query(False),
):
    return jsonable_encoder(
        search_indexed_open_access_sources(
            query=q,
            limit=limit,
            offset=offset,
            source_system=source_system,
            summary_ready_only=summary_ready_only,
        )
    )


@router.get("/open-access/runs")
def open_access_runs(limit: int = Query(20, ge=1, le=100)):
    return jsonable_encoder({
        "runs": list_open_access_ingestion_runs(limit=limit),
    })
