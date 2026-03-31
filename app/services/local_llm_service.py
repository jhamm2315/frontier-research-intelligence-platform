import os

import requests

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral")
OLLAMA_KEEP_ALIVE = os.getenv("OLLAMA_KEEP_ALIVE", "10m")
OLLAMA_NUM_PREDICT = os.getenv("OLLAMA_NUM_PREDICT")
OLLAMA_TEMPERATURE = os.getenv("OLLAMA_TEMPERATURE")
_SESSION = requests.Session()


def call_ollama(prompt: str, model: str = OLLAMA_MODEL, timeout: int = 180) -> str:
    options = {}
    if OLLAMA_NUM_PREDICT:
        try:
            options["num_predict"] = int(OLLAMA_NUM_PREDICT)
        except ValueError:
            pass
    if OLLAMA_TEMPERATURE:
        try:
            options["temperature"] = float(OLLAMA_TEMPERATURE)
        except ValueError:
            pass

    response = _SESSION.post(
        OLLAMA_URL,
        json={
            "model": model,
            "prompt": prompt,
            "stream": False,
            "keep_alive": OLLAMA_KEEP_ALIVE,
            "options": options or None,
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
def generate_local_llm_summary(prompt: str) -> str:
    """
    Compatibility wrapper for multi-paper comparison and any other services
    that expect a standardized local LLM summary function.

    This function tries several likely local LLM entrypoints already present
    in this module and normalizes the return value to a string.
    """
    candidate_names = [
        "ask_local_llm",
        "query_local_llm",
        "run_local_llm",
        "call_local_llm",
        "generate_summary",
        "generate_with_ollama",
        "prompt_ollama",
        "call_ollama",
        "chat_with_ollama",
        "invoke_ollama",
    ]

    for name in candidate_names:
        fn = globals().get(name)
        if callable(fn):
            result = fn(prompt)

            if result is None:
                return ""

            if isinstance(result, str):
                return result

            if isinstance(result, dict):
                return (
                    result.get("response")
                    or result.get("answer")
                    or result.get("summary")
                    or result.get("text")
                    or str(result)
                )

            return str(result)

    raise RuntimeError(
        "No compatible local LLM function was found in app.services.local_llm_service. "
        "Expected one of: ask_local_llm, query_local_llm, run_local_llm, call_local_llm, "
        "generate_summary, generate_with_ollama, prompt_ollama, call_ollama, "
        "chat_with_ollama, invoke_ollama."
    )
