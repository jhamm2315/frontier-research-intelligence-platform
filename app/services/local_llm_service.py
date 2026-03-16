import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "mistral"


def call_ollama(prompt: str, model: str = OLLAMA_MODEL, timeout: int = 180) -> str:
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": model,
            "prompt": prompt,
            "stream": False
        },
        timeout=timeout
    )
    response.raise_for_status()
    data = response.json()
    return data.get("response", "").strip()


def generate_paper_summary(text: str) -> str:
    prompt = f"""
You are an academic research assistant.

Analyze the following research paper and produce structured output.

Provide these sections with clear headings:

Plain English Summary:
Academic Summary:
Key Methods:
Key Results:
Limitations:
Practical Applications:
Suggested Research Topics:
Citation Guidance:

Paper:
{text[:7000]}
"""
    return call_ollama(prompt, timeout=240)


def answer_question_with_context(question: str, context_chunks: list[dict]) -> dict:
    if not context_chunks:
        return {
            "answer": "No relevant source material was found for this question.",
            "evidence": []
        }

    context_text_parts = []
    evidence = []

    for idx, chunk in enumerate(context_chunks, start=1):
        text = chunk.get("text", "").strip()
        section = chunk.get("section_guess", "unknown")
        score = chunk.get("score", 0)
        chunk_id = chunk.get("chunk_id", "")
        document_id = chunk.get("document_id", "")

        if text:
            context_text_parts.append(
                f"[Source {idx} | document_id={document_id} | chunk_id={chunk_id} | section={section} | score={score}]\n{text}"
            )

        evidence.append({
            "document_id": document_id,
            "chunk_id": chunk_id,
            "section_guess": section,
            "score": score,
            "text": text[:500]
        })

    context_blob = "\n\n".join(context_text_parts)

    prompt = f"""
You are a research paper assistant.

Answer the user's question using ONLY the provided source excerpts.
Write the answer in clear, human-friendly language suitable for students and researchers.
If the evidence is incomplete, say so clearly.
Do not invent facts not supported by the excerpts.

User question:
{question}

Source excerpts:
{context_blob}

Return only the answer text.
"""

    answer = call_ollama(prompt, timeout=180)

    return {
        "answer": answer,
        "evidence": evidence
    }
