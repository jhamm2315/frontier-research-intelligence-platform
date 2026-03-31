from pathlib import Path

import numpy as np
import pandas as pd
from fastapi import APIRouter, UploadFile, File, Query
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel

from app.api.product import _UPLOADED_DOCUMENTS
from app.services.document_ingestion_service import ingest_existing_file
from app.services.local_llm_service import (
    answer_question_with_context,
    generate_local_llm_summary,
)
from app.services.retrieval_service import retrieve_relevant_chunks
from app.services.recommendation_tracking_service import (
    safe_track_recommendation_activity_for_user,
)

router = APIRouter()

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"


def clean_for_json(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df = df.replace([np.inf, -np.inf], np.nan)
    df = df.astype(object)
    df = df.where(pd.notnull(df), None)
    return df


class QuestionRequest(BaseModel):
    question: str
    document_id: str | None = None
    user_id: str | None = None


class IngestRequest(BaseModel):
    file_path: str
    title: str
    author: str = "Unknown"
    institution: str = "Unknown"
    topic: str = "Unknown"
    citation: str = ""


@router.get("/health")
def documents_health():
    return {"status": "documents api ok"}


@router.get("/list")
def list_documents():
    path = PROCESSED_DIR / "document_registry.csv"
    if not path.exists():
        return []

    df = pd.read_csv(path)
    df = clean_for_json(df)
    return jsonable_encoder(df.to_dict(orient="records"))


@router.get("/{document_id}/summary")
def get_document_summary(
    document_id: str,
    user_id: str | None = Query(None, description="Optional active user identifier"),
):
    reg_path = PROCESSED_DIR / "document_registry.csv"
    sum_path = PROCESSED_DIR / "document_summaries.csv"

    if not reg_path.exists() or not sum_path.exists():
        return {"message": "Document summary data not available."}

    registry = pd.read_csv(reg_path)
    summaries = pd.read_csv(sum_path)

    reg_row = registry.loc[registry["document_id"] == document_id]
    sum_row = summaries.loc[summaries["document_id"] == document_id]

    if reg_row.empty:
        return {"message": f"Document {document_id} not found."}

    reg = clean_for_json(reg_row).iloc[0].to_dict()
    summ = clean_for_json(sum_row).iloc[0].to_dict() if not sum_row.empty else {}

    response = {
        "document_id": reg.get("document_id"),
        "title": reg.get("title"),
        "author": reg.get("author"),
        "institution": reg.get("institution"),
        "topic": reg.get("topic"),
        "citation": reg.get("citation"),
        "source_system": reg.get("source_system"),
        "source_paper_id": reg.get("source_paper_id"),
        "published": reg.get("published"),
        "updated": reg.get("updated"),
        "pdf_url": reg.get("pdf_url"),
        "entry_url": reg.get("entry_url"),
        "categories": reg.get("categories"),
        "file_name": reg.get("file_name"),
        "plain_english_summary": summ.get("plain_english_summary", ""),
        "academic_summary": summ.get("academic_summary", ""),
        "executive_summary": summ.get("executive_summary", ""),
        "technical_summary": summ.get("technical_summary", ""),
        "methods_summary": summ.get("methods_summary", ""),
        "results_summary": summ.get("results_summary", ""),
        "limitations_summary": summ.get("limitations_summary", ""),
        "conclusion_summary": summ.get("conclusion_summary", ""),
        "practical_applications": summ.get("practical_applications", ""),
        "suggested_topics": summ.get("suggested_topics", ""),
        "citation_guidance": summ.get("citation_guidance", ""),
    }

    safe_track_recommendation_activity_for_user(
        user_id,
        "view",
        {
            "work_id": reg.get("work_id") or reg.get("source_paper_id") or document_id,
            "document_id": reg.get("document_id"),
            "title": reg.get("title"),
            "author": reg.get("author"),
            "institution": reg.get("institution"),
            "topic": reg.get("topic"),
            "source_system": reg.get("source_system"),
            "event_source": "documents.summary",
            "action_context": "document_summary_view",
        },
    )

    return jsonable_encoder(response)


@router.post("/ingest-existing")
def ingest_existing_document(payload: IngestRequest):
    result = ingest_existing_file(
        file_path=payload.file_path,
        title=payload.title,
        author=payload.author,
        institution=payload.institution,
        topic=payload.topic,
        citation=payload.citation,
    )
    return jsonable_encoder(result)


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    return {
        "filename": file.filename,
        "message": "Document upload endpoint scaffolded."
    }


@router.post("/summarize")
def summarize_document():
    return {"message": "Document summarization endpoint scaffolded."}


@router.post("/ask")
def ask_document_question(payload: QuestionRequest):
    document_id = payload.document_id
    question = payload.question

    # --- Handle uploaded documents ---
    if document_id and str(document_id).startswith("uploaded_"):
        uploaded_doc = _UPLOADED_DOCUMENTS.get(document_id)

        if not uploaded_doc:
            return jsonable_encoder({
                "question": question,
                "answer": "Uploaded document not found.",
                "evidence": []
            })

        content = uploaded_doc.get("content", "") or ""
        metadata = uploaded_doc.get("metadata", {}) or {}

        if not content.strip():
            return jsonable_encoder({
                "question": question,
                "answer": "This uploaded document does not have extracted text available yet.",
                "evidence": []
            })

        prompt = f'''
You are a research assistant answering questions about an uploaded document.

Document Title:
{metadata.get("title", "Uploaded Document")}

Question:
{question}

Document Content:
{content[:12000]}

Instructions:
- Answer only using the uploaded document content
- Be clear and helpful
- If the answer is not explicit, say that clearly
- Keep the answer concise but informative
'''

        llm_answer = generate_local_llm_summary(prompt)

        safe_track_recommendation_activity_for_user(
            payload.user_id,
            "question",
            {
                **metadata,
                "document_id": document_id,
                "search_query": question,
                "event_source": "documents.ask",
                "action_context": "uploaded_document_question",
            },
        )

        return jsonable_encoder({
            "question": question,
            "answer": llm_answer,
            "evidence": [
                {
                    "document_id": document_id,
                    "chunk_id": "uploaded_full_text",
                    "section_guess": "uploaded_document",
                    "score": 1.0,
                    "text": content[:1200]
                }
            ]
        })

    # --- Default retrieval pipeline ---
    chunks = retrieve_relevant_chunks(
        query=question,
        document_id=document_id,
        top_k=4
    )

    result = answer_question_with_context(question, chunks)

    safe_track_recommendation_activity_for_user(
        payload.user_id,
        "question",
        {
            "document_id": document_id,
            "search_query": question,
            "event_source": "documents.ask",
            "action_context": "document_question",
            "metadata": {
                "evidence_document_ids": [
                    chunk.get("document_id")
                    for chunk in result.get("evidence", [])
                    if chunk.get("document_id")
                ][:5]
            },
        },
    )

    return jsonable_encoder({
        "question": question,
        "answer": result.get("answer", ""),
        "evidence": result.get("evidence", [])
    })


@router.post("/compare")
def compare_documents():
    return {"message": "Document comparison endpoint scaffolded."}
