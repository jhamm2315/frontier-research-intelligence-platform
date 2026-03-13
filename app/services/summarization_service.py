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

    ordered_text = []
    seen = set()

    for chunk in chunks:
        text = chunk.get("text", "").strip()
        if text and text not in seen:
            ordered_text.append(text)
            seen.add(text)

    combined = " ".join(ordered_text)

    abstract = extract_section(combined, "abstract")
    methods = extract_section(combined, "methods")
    results = extract_section(combined, "results")
    limitations = extract_section(combined, "limitations")
    conclusion = extract_section(combined, "conclusion")

    lower_q = question.lower()

    if "method" in lower_q:
        answer = methods or abstract or combined[:900]
    elif "result" in lower_q or "find" in lower_q:
        answer = results or abstract or combined[:900]
    elif "limitation" in lower_q or "weakness" in lower_q:
        answer = limitations or combined[:900]
    elif "conclusion" in lower_q or "conclude" in lower_q:
        answer = conclusion or results or combined[:900]
    elif "what is this paper about" in lower_q or "summary" in lower_q or "about" in lower_q:
        answer_parts = [part for part in [abstract, methods, results, conclusion] if part]
        answer = " ".join(answer_parts)[:1200] if answer_parts else combined[:1200]
    else:
        answer_parts = [part for part in [abstract, methods, results, limitations, conclusion] if part]
        answer = " ".join(answer_parts)[:1200] if answer_parts else combined[:1200]

    return {
        "question": question,
        "answer": answer.strip(),
        "evidence": [
            {
                "document_id": c["document_id"],
                "chunk_id": c["chunk_id"],
                "section_guess": c["section_guess"],
                "score": c["score"],
                "text": c["text"][:500].strip(),
            }
            for c in chunks
        ],
    }
