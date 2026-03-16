from pathlib import Path
import pandas as pd
import numpy as np
from fastapi import APIRouter, UploadFile, File
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel

from app.services.retrieval_service import retrieve_relevant_chunks
from app.services.document_ingestion_service import ingest_existing_file
from app.services.local_llm_service import answer_question_with_context

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
def get_document_summary(document_id: str):
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

    return jsonable_encoder({
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
    })


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
    chunks = retrieve_relevant_chunks(
        query=payload.question,
        document_id=payload.document_id,
        top_k=4
    )

    result = answer_question_with_context(payload.question, chunks)
    return jsonable_encoder({
        "question": payload.question,
        "answer": result.get("answer", ""),
        "evidence": result.get("evidence", [])
    })


@router.post("/compare")
def compare_documents():
    return {"message": "Document comparison endpoint scaffolded."}
