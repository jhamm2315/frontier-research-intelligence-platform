from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parents[1]

RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
VECTOR_DIR = BASE_DIR / "data" / "vector_store"
DOCS_DIR = BASE_DIR / "docs"
MODELS_DIR = BASE_DIR / "models"
LOG_DIR = BASE_DIR / "logs"

for d in [RAW_DIR, PROCESSED_DIR, VECTOR_DIR, DOCS_DIR, MODELS_DIR, LOG_DIR]:
    d.mkdir(parents=True, exist_ok=True)

DUCKDB_PATH = BASE_DIR / "frontier_research.duckdb"

OPENALEX_EMAIL = os.getenv("OPENALEX_EMAIL", "")
SEMANTIC_SCHOLAR_API_KEY = os.getenv("SEMANTIC_SCHOLAR_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

OPENALEX_WORKS_PATH = RAW_DIR / "openalex_works_sample.csv"
PROFILE_OUTPUT_PATH = DOCS_DIR / "data_profile.xlsx"
SCHEMA_REPORT_PATH = DOCS_DIR / "schema_validation_report.csv"

EXPECTED_WORK_COLUMNS = [
    "id",
    "doi",
    "title",
    "publication_year",
    "cited_by_count",
    "concepts",
    "authorships",
    "institutions_distinct_count",
]

OPENALEX_SAMPLE_TOPICS = [
    "artificial intelligence",
    "quantum computing",
    "gene editing",
    "battery materials",
    "climate modeling",
]

OPENALEX_PER_TOPIC = 40
OPENALEX_BASE_URL = "https://api.openalex.org/works"
