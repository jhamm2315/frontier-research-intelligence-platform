from fastapi import APIRouter, UploadFile, File, Body
from pydantic import BaseModel

from app.services.retrieval_service import retrieve_relevant_chunks
from app.services.summarization_service import answer_question_from_chunks

router = APIRouter()


class QuestionRequest(BaseModel):
    question: str
    document_id: str | None = None


@router.get("/health")
def documents_health():
    return {"status": "documents api ok"}


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
