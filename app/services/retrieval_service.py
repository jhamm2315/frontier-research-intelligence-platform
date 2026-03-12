from pathlib import Path
import pandas as pd
import re

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CHUNKS_PATH = PROJECT_ROOT / "data" / "processed" / "document_chunks.csv"


def tokenize(text: str) -> set[str]:
    if not text:
        return set()
    return set(re.findall(r"[A-Za-z0-9\-]+", text.lower()))


def score_chunk(query_tokens: set[str], chunk_text: str) -> int:
    chunk_tokens = tokenize(chunk_text)
    return len(query_tokens.intersection(chunk_tokens))


def retrieve_relevant_chunks(query: str, document_id: str | None = None, top_k: int = 3) -> list[dict]:
    if not CHUNKS_PATH.exists():
        return []

    chunks = pd.read_csv(CHUNKS_PATH)

    if document_id:
        chunks = chunks.loc[chunks["document_id"] == document_id].copy()

    query_tokens = tokenize(query)

    if not query_tokens:
        return []

    chunks["retrieval_score"] = chunks["chunk_text"].astype(str).apply(
        lambda txt: score_chunk(query_tokens, txt)
    )

    ranked = (
        chunks.loc[chunks["retrieval_score"] > 0]
        .sort_values(["retrieval_score", "chunk_char_count"], ascending=[False, False])
        .head(top_k)
    )

    results = []
    for _, row in ranked.iterrows():
        results.append({
            "document_id": row["document_id"],
            "chunk_id": row["chunk_id"],
            "chunk_order": row["chunk_order"],
            "section_guess": row["section_guess"],
            "text": row["chunk_text"],
            "score": int(row["retrieval_score"]),
        })

    return results
