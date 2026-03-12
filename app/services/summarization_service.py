import re


SECTION_PATTERNS = {
    "abstract": r"(abstract:)(.*?)(methods:|results:|limitations:|conclusion:|$)",
    "methods": r"(methods:)(.*?)(results:|limitations:|conclusion:|$)",
    "results": r"(results:)(.*?)(limitations:|conclusion:|$)",
    "limitations": r"(limitations:)(.*?)(conclusion:|$)",
    "conclusion": r"(conclusion:)(.*)$",
}


def extract_section(text: str, section_name: str) -> str:
    if not text:
        return ""

    pattern = SECTION_PATTERNS.get(section_name)
    if not pattern:
        return ""

    match = re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        return ""

    if len(match.groups()) >= 2:
        section_text = match.group(2).strip()
    else:
        section_text = match.group(0).strip()

    return " ".join(section_text.split())


def summarize_text(text: str, mode: str = "executive") -> dict:
    text = " ".join(text.split()) if text else ""

    abstract = extract_section(text, "abstract")
    methods = extract_section(text, "methods")
    results = extract_section(text, "results")
    limitations = extract_section(text, "limitations")
    conclusion = extract_section(text, "conclusion")

    if mode == "executive":
        summary = " ".join(
            part for part in [
                abstract[:350],
                results[:250],
                conclusion[:200],
            ] if part
        ).strip()
    elif mode == "technical":
        summary = " ".join(
            part for part in [
                abstract[:250],
                methods[:350],
                results[:300],
                limitations[:250],
            ] if part
        ).strip()
    else:
        summary = text[:600]

    return {
        "mode": mode,
        "summary": summary,
        "abstract": abstract,
        "methods": methods,
        "results": results,
        "limitations": limitations,
        "conclusion": conclusion,
    }

def answer_question_from_chunks(question: str, chunks: list[dict]) -> dict:
    if not chunks:
        return {
            "question": question,
            "answer": "No relevant source material was found for this question.",
            "evidence": [],
        }

    top_chunk = chunks[0]
    answer = top_chunk["text"][:700].strip()

    return {
        "question": question,
        "answer": answer,
        "evidence": [
            {
                "document_id": c["document_id"],
                "chunk_id": c["chunk_id"],
                "section_guess": c["section_guess"],
                "score": c["score"],
                "text": c["text"][:400].strip(),
            }
            for c in chunks
        ],
    }
