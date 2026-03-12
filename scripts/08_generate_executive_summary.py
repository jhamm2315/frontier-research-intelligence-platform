from pathlib import Path
import sys
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from config.settings import PROCESSED_DIR


def main():
    rankings = pd.read_csv(PROCESSED_DIR / "research_rankings_summary.csv")
    breakthrough = pd.read_csv(PROCESSED_DIR / "top_breakthrough_candidates.csv")
    topics = pd.read_csv(PROCESSED_DIR / "top_emerging_topics.csv")
    authors = pd.read_csv(PROCESSED_DIR / "top_rising_authors.csv")
    institutions = pd.read_csv(PROCESSED_DIR / "top_rising_institutions.csv")

    registry = pd.read_csv(PROCESSED_DIR / "document_registry.csv")
    chunks = pd.read_csv(PROCESSED_DIR / "document_chunks.csv")
    summaries = pd.read_csv(PROCESSED_DIR / "document_summaries.csv")
    qa = pd.read_csv(PROCESSED_DIR / "document_qa_results.csv")

    total_works = rankings.loc[rankings["metric"] == "total_works", "value"].iloc[0]
    total_authors = rankings.loc[rankings["metric"] == "total_authors", "value"].iloc[0]
    total_institutions = rankings.loc[rankings["metric"] == "total_institutions", "value"].iloc[0]
    total_topics = rankings.loc[rankings["metric"] == "total_topics", "value"].iloc[0]

    top_breakthrough_title = rankings.loc[rankings["metric"] == "top_breakthrough_title", "value"].iloc[0]
    top_emerging_topic = rankings.loc[rankings["metric"] == "top_emerging_topic", "value"].iloc[0]
    top_rising_author = rankings.loc[rankings["metric"] == "top_rising_author", "value"].iloc[0]
    top_rising_institution = rankings.loc[rankings["metric"] == "top_rising_institution", "value"].iloc[0]

    top_breakthrough_score = float(breakthrough.iloc[0]["breakthrough_rank_score"]) if not breakthrough.empty else 0.0
    top_topic_score = float(topics.iloc[0]["emerging_topic_score"]) if not topics.empty else 0.0
    top_author_score = float(authors.iloc[0]["rising_author_score"]) if not authors.empty else 0.0
    top_institution_score = float(institutions.iloc[0]["rising_institution_score"]) if not institutions.empty else 0.0

    total_documents = len(registry)
    total_chunks = len(chunks)
    total_qa_tests = len(qa)

    avg_chunks_per_doc = round(total_chunks / total_documents, 2) if total_documents else 0.0
    avg_evidence_count = round(qa["evidence_count"].mean(), 2) if "evidence_count" in qa.columns and len(qa) else 0.0

    signal_summary = pd.DataFrame([
        {"metric": "total_works", "value": total_works},
        {"metric": "total_authors", "value": total_authors},
        {"metric": "total_institutions", "value": total_institutions},
        {"metric": "total_topics", "value": total_topics},
        {"metric": "total_documents", "value": total_documents},
        {"metric": "total_chunks", "value": total_chunks},
        {"metric": "avg_chunks_per_document", "value": avg_chunks_per_doc},
        {"metric": "total_qa_tests", "value": total_qa_tests},
        {"metric": "avg_qa_evidence_count", "value": avg_evidence_count},
        {"metric": "top_breakthrough_title", "value": top_breakthrough_title},
        {"metric": "top_emerging_topic", "value": top_emerging_topic},
        {"metric": "top_rising_author", "value": top_rising_author},
        {"metric": "top_rising_institution", "value": top_rising_institution},
    ])

    top_signals = pd.DataFrame([
        {
            "signal_type": "breakthrough_candidate",
            "label": top_breakthrough_title,
            "score": round(top_breakthrough_score, 4),
            "context": breakthrough.iloc[0]["primary_topic"] if not breakthrough.empty else "",
        },
        {
            "signal_type": "emerging_topic",
            "label": top_emerging_topic,
            "score": round(top_topic_score, 4),
            "context": "",
        },
        {
            "signal_type": "rising_author",
            "label": top_rising_author,
            "score": round(top_author_score, 4),
            "context": "",
        },
        {
            "signal_type": "rising_institution",
            "label": top_rising_institution,
            "score": round(top_institution_score, 4),
            "context": "",
        },
    ])

    executive_summary = f"""
Frontier Research Intelligence Platform — Executive Summary

Platform scope:
- Works analyzed: {total_works}
- Authors extracted: {total_authors}
- Institutions extracted: {total_institutions}
- Topics extracted: {total_topics}
- Research documents ingested: {total_documents}
- Document chunks indexed: {total_chunks}
- Q&A test cases completed: {total_qa_tests}

Top platform signals:
- Top breakthrough candidate: {top_breakthrough_title}
- Top emerging topic: {top_emerging_topic}
- Top rising author: {top_rising_author}
- Top rising institution: {top_rising_institution}

Document intelligence summary:
- Average chunks per document: {avg_chunks_per_doc}
- Average evidence count returned in Q&A: {avg_evidence_count}

Leadership interpretation:
The platform is now operating across two core intelligence layers: a scholarly graph layer that identifies high-signal research entities, and a document intelligence layer that can summarize papers and answer grounded questions from source material. Together, these modules provide the foundation for a scientific discovery system that can surface influential work, identify emerging fields, and reduce the time required to understand complex research documents.

Recommended next steps:
1. Build a stronger ranking model that favors recent momentum over legacy citation dominance.
2. Add semantic retrieval and vector search for more robust document question answering.
3. Introduce novelty and interdisciplinarity scoring for breakthrough prediction.
4. Build the interactive explorer so users can visually inspect topics, authors, institutions, and paper relationships.
5. Package the platform with a polished notebook and executive-facing README for portfolio and client presentation.
""".strip()

    summary_txt_path = PROCESSED_DIR / "executive_research_summary.txt"
    signal_csv_path = PROCESSED_DIR / "platform_signal_summary.csv"
    top_signals_path = PROCESSED_DIR / "top_platform_signals.csv"

    summary_txt_path.write_text(executive_summary)
    signal_summary.to_csv(signal_csv_path, index=False)
    top_signals.to_csv(top_signals_path, index=False)

    print("Executive platform summary generation complete.\n")
    print("Saved outputs:")
    print("-", summary_txt_path)
    print("-", signal_csv_path)
    print("-", top_signals_path)

    print("\nExecutive summary:")
    print(executive_summary)

    print("\nSignal summary table:")
    print(signal_summary)

    print("\nTop platform signals:")
    print(top_signals)


if __name__ == "__main__":
    main()
