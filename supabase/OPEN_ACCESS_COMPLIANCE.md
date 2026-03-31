# Open-Access Ingestion Boundaries

This repo now includes a foundation for ingesting only clearly open/public scholarly sources into Supabase.

## What is supported now

- API-first search from:
  - arXiv
  - OpenAlex global open-access works
  - OpenAlex-backed institutional results from a broader international university set
  - Europe PMC open-access records
  - DOAJ article search
  - Harvard LibraryCloud
- Single-page polite ingestion for manually supplied URLs on allowlisted academic/open-access hosts
- Provenance, access-basis, rights, and asset-link storage in:
  - `open_access_sources`
  - `open_access_source_assets`
  - `open_access_ingestion_runs`

## Compliance boundaries

- No paywall bypassing
- No recursive crawling
- No aggressive scraping
- No evasion of robots, auth walls, or rate limits
- No assumption that public availability equals unrestricted redistribution

## Runtime allowlist

- Curated hosts are built into `app/services/open_access_ingestion_service.py`
- Additional reviewed hosts can be added with:
  - `OPEN_ACCESS_ALLOWED_HOSTS=repo.example.edu,archive.example.ac.uk`

Only hosts on the built-in list or approved academic suffixes are accepted for manual URL ingestion.

## Scheduled indexing

Automatic indexing can be enabled with environment variables:

- `OPEN_ACCESS_AUTO_INDEX_ENABLED=true`
- `OPEN_ACCESS_AUTO_INDEX_QUERIES=graph neural networks,protein folding,causal inference`
- `OPEN_ACCESS_AUTO_INDEX_INTERVAL_MINUTES=360`
- `OPEN_ACCESS_AUTO_INDEX_PAGES=2`
- `OPEN_ACCESS_AUTO_INDEX_LIMIT_PER_SOURCE=25`
- `OPEN_ACCESS_AUTO_INDEX_STARTUP_DELAY_SECONDS=30`
- `OPEN_ACCESS_AUTO_INDEX_SOURCE_INTERVALS=openalex_global:90,europe_pmc:120,arxiv:240,openalex_institutions:360,doaj:720,harvard_librarycloud:1440`
- `OPEN_ACCESS_AUTO_INDEX_SOURCE_QUERIES=openalex_global=artificial intelligence|climate risk|quantum computing;europe_pmc=cancer biomarkers|genome sequencing|drug discovery;doaj=digital humanities|education policy|urban studies`

Supported per-source cadence keys:

- `openalex_global`
- `openalex_institutions`
- `europe_pmc`
- `doaj`
- `harvard_librarycloud`
- `arxiv`

Suggested source-specific query lanes:

- `openalex_global`
  - broad discovery themes like AI, climate, robotics, quantum, materials, policy, economics
- `europe_pmc`
  - biomedical topics like oncology, genomics, proteomics, therapeutics, epidemiology
- `doaj`
  - journal-heavy interdisciplinary topics like education, humanities, law, sustainability, media studies

This scheduler uses the same open/public connector boundaries as manual indexing:

- API-first collection only
- reviewed open/public sources only
- no recursive crawling
- no paywall bypassing

## Important review notes

- `license_name`, `license_url`, `rights_statement`, and `usage_constraints` are stored when discoverable, but some sources will still require manual review before full-text republication, translation, or asset redistribution.
- Diagram/image links are stored only when they are directly discoverable from the source page. Their presence does not automatically grant republishing rights.
- Search endpoints return verified source URLs and metadata. Applying the schema to the live Supabase project is still a separate step.
- Broad search does not mean indiscriminate scraping:
  - large result sets should come from paginated open/public APIs and reviewed repositories
  - manual URL ingestion still stays allowlist-based
  - sources must remain clearly open/public and user-readable
