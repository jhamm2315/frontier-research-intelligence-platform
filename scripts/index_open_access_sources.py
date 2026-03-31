from __future__ import annotations

import argparse
import json

from app.services.open_access_index_service import collect_open_access_index


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Batch index open-access sources into the Frontier catalog.")
    parser.add_argument("query", help="Search query to index")
    parser.add_argument("--pages", type=int, default=3, help="Number of paged result batches to collect")
    parser.add_argument("--limit-per-source", type=int, default=50, help="Result limit per connector per page")
    parser.add_argument("--user-id", default=None, help="Optional Clerk user id for run attribution")
    parser.add_argument("--mark-featured", action="store_true", help="Mark ingested records as featured")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = collect_open_access_index(
        query=args.query,
        pages=args.pages,
        limit_per_source=args.limit_per_source,
        requested_by_clerk_user_id=args.user_id,
        mark_featured=args.mark_featured,
    )
    print(json.dumps({
        "success": result.get("success"),
        "query": result.get("query"),
        "record_count": result.get("record_count"),
        "warning_count": result.get("warning_count"),
        "ingestion_run": result.get("ingestion_run", {}).get("id"),
    }, indent=2))


if __name__ == "__main__":
    main()
