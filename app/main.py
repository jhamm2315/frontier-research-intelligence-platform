from fastapi import FastAPI
from app.api import documents, research

app = FastAPI(
    title="Frontier Research Intelligence Platform",
    version="0.1.0",
    description="Scientific discovery intelligence system with graph analytics, document intelligence, and research question answering."
)

app.include_router(documents.router, prefix="/documents", tags=["Documents"])
app.include_router(research.router, prefix="/research", tags=["Research"])


@app.get("/")
def root():
    return {
        "message": "Frontier Research Intelligence Platform API is running."
    }
