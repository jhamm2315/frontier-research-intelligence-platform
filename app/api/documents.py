from pathlib import Path
import pandas as pd
from fastapi import APIRouter, UploadFile, File
from pydantic import BaseModel

from app.services.retrieval_service import retrieve_relevant_chunks
from app.services.summarization_service import answer_question_from_chunks
from app.services.document_ingestion_service import ingest_existing_file

router = APIRouter()

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"


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
    return df.to_dict(orient="records")


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

    reg = reg_row.iloc[0].to_dict()
    summ = sum_row.iloc[0].to_dict() if not sum_row.empty else {}

    return {
        "document_id": reg.get("document_id"),
        "title": reg.get("title"),
        "author": reg.get("author"),
        "institution": reg.get("institution"),
        "topic": reg.get("topic"),
        "citation": reg.get("citation"),
        "file_name": reg.get("file_name"),
        "executive_summary": summ.get("executive_summary", ""),
        "technical_summary": summ.get("technical_summary", ""),
        "methods_summary": summ.get("methods_summary", ""),
        "results_summary": summ.get("results_summary", ""),
        "limitations_summary": summ.get("limitations_summary", ""),
        "conclusion_summary": summ.get("conclusion_summary", ""),
    }


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
    return result


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
        top_k=3
    )
    result = answer_question_from_chunks(payload.question, chunks)
    return result


@router.post("/compare")
def compare_documents():
    return {"message": "Document comparison endpoint scaffolded."}
