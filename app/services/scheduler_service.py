from __future__ import annotations

from datetime import datetime, timedelta, timezone
import threading
from typing import Any

from app.config import Settings
from app.services.open_access_index_service import collect_open_access_index


DEFAULT_SOURCE_INTERVALS = {
    "arxiv": 240,
    "openalex_global": 90,
    "openalex_institutions": 360,
    "europe_pmc": 120,
    "doaj": 720,
    "harvard_librarycloud": 1440,
}


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class OpenAccessAutoIndexer:
    def __init__(self) -> None:
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()
        self._started = False
        self._settings: Settings | None = None
        self._status: dict[str, Any] = {
            "running": False,
            "started_at": None,
            "last_started_at": None,
            "last_completed_at": None,
            "last_success_at": None,
            "last_error": None,
            "last_run_summaries": [],
            "total_runs": 0,
            "source_jobs": {},
        }

    def start(self, settings: Settings) -> None:
        with self._lock:
            if self._started:
                return
            self._settings = settings
            self._stop_event.clear()
            self._thread = threading.Thread(
                target=self._run_loop,
                name="open-access-auto-indexer",
                daemon=True,
            )
            self._started = True
            self._status["running"] = True
            self._status["started_at"] = _utcnow_iso()
            self._status["source_jobs"] = self._build_source_job_status(settings)
            self._thread.start()

    def stop(self) -> None:
        with self._lock:
            if not self._started:
                return
            self._stop_event.set()
            thread = self._thread
            self._started = False
            self._status["running"] = False
        if thread and thread.is_alive():
            thread.join(timeout=5)

    def status(self) -> dict[str, Any]:
        with self._lock:
            settings = self._settings
            return {
                **self._status,
                "enabled": bool(settings and settings.auto_index_enabled and settings.has_auto_index_queries),
                "pages": settings.auto_index_pages if settings else None,
                "limit_per_source": settings.auto_index_limit_per_source if settings else None,
                "queries": list(settings.auto_index_queries) if settings else [],
                "source_intervals": self._effective_source_intervals(settings) if settings else {},
                "source_queries": self._effective_source_queries(settings) if settings else {},
            }

    def _effective_source_intervals(self, settings: Settings | None) -> dict[str, int]:
        merged = DEFAULT_SOURCE_INTERVALS.copy()
        if settings and settings.auto_index_source_intervals:
            merged.update(settings.auto_index_source_intervals)
        return merged

    def _build_source_job_status(self, settings: Settings) -> dict[str, Any]:
        now = _utcnow_iso()
        return {
            source: {
                "interval_minutes": interval,
                "queries": list(self._queries_for_source(settings, source)),
                "last_started_at": None,
                "last_completed_at": None,
                "last_success_at": None,
                "last_error": None,
                "last_duration_ms": None,
                "last_record_count": 0,
                "last_warning_count": 0,
                "total_records_indexed": 0,
                "total_warning_count": 0,
                "total_failure_count": 0,
                "manual_runs": 0,
                "next_due_at": now,
                "total_runs": 0,
            }
            for source, interval in self._effective_source_intervals(settings).items()
        }

    def _effective_source_queries(self, settings: Settings | None) -> dict[str, list[str]]:
        if not settings:
            return {}
        return {
            source: list(self._queries_for_source(settings, source))
            for source in self._effective_source_intervals(settings).keys()
        }

    def _queries_for_source(self, settings: Settings, source: str) -> tuple[str, ...]:
        if settings.auto_index_source_queries and source in settings.auto_index_source_queries:
            return settings.auto_index_source_queries[source]
        return settings.auto_index_queries

    def _run_loop(self) -> None:
        settings = self._settings
        if not settings:
            return

        if settings.auto_index_startup_delay_seconds:
            if self._stop_event.wait(settings.auto_index_startup_delay_seconds):
                return

        while not self._stop_event.is_set():
            self._run_due_sources(settings)
            if self._stop_event.wait(30):
                break

    def _run_due_sources(self, settings: Settings) -> None:
        now = datetime.now(timezone.utc)
        source_jobs = self._status.setdefault("source_jobs", {})
        summaries: list[dict[str, Any]] = []
        errors: list[str] = []
        any_success = False

        for source, interval in self._effective_source_intervals(settings).items():
            source_queries = self._queries_for_source(settings, source)
            job_status = source_jobs.setdefault(source, {
                "interval_minutes": interval,
                "queries": list(source_queries),
                "last_started_at": None,
                "last_completed_at": None,
                "last_success_at": None,
                "last_error": None,
                "last_duration_ms": None,
                "last_record_count": 0,
                "last_warning_count": 0,
                "total_records_indexed": 0,
                "total_warning_count": 0,
                "total_failure_count": 0,
                "manual_runs": 0,
                "next_due_at": _utcnow_iso(),
                "total_runs": 0,
            })
            job_status["interval_minutes"] = interval
            job_status["queries"] = list(source_queries)

            if not source_queries:
                job_status["last_error"] = "No queries configured for this source."
                continue

            next_due_at = self._parse_dt(job_status.get("next_due_at"))
            if next_due_at and next_due_at > now:
                continue

            run_result = self._run_source_queries(
                settings=settings,
                source=source,
                source_queries=source_queries,
                requested_by_clerk_user_id="system_auto_indexer",
                manual=False,
            )
            source_success = run_result["success"]
            source_record_count = run_result["record_count"]
            source_warning_count = run_result["warning_count"]
            summaries.extend(run_result["summaries"])
            errors.extend(run_result["errors"])

            job_status["next_due_at"] = self._shift_minutes(interval)
            if source_success:
                any_success = True
                job_status["last_success_at"] = job_status["last_completed_at"]
                job_status["last_error"] = None
            elif source_warning_count:
                job_status["last_error"] = f"{source_warning_count} warning(s) in last run"

        if summaries:
            self._status["last_run_summaries"] = summaries[:50]
            self._status["last_completed_at"] = _utcnow_iso()
            if errors:
                self._status["last_error"] = " | ".join(errors[:20])
            else:
                self._status["last_error"] = None
            if any_success:
                self._status["last_success_at"] = self._status["last_completed_at"]

    def _run_source_queries(
        self,
        settings: Settings,
        source: str,
        source_queries: tuple[str, ...],
        requested_by_clerk_user_id: str,
        manual: bool,
    ) -> dict[str, Any]:
        source_jobs = self._status.setdefault("source_jobs", {})
        job_status = source_jobs[source]
        started_at = datetime.now(timezone.utc)
        started_at_iso = started_at.isoformat()
        self._status["last_started_at"] = started_at_iso
        job_status["last_started_at"] = started_at_iso
        job_status["total_runs"] += 1
        self._status["total_runs"] += 1
        if manual:
            job_status["manual_runs"] += 1

        source_success = False
        source_record_count = 0
        source_warning_count = 0
        summaries: list[dict[str, Any]] = []
        errors: list[str] = []

        for query in source_queries:
            try:
                result = collect_open_access_index(
                    query=query,
                    pages=settings.auto_index_pages,
                    limit_per_source=settings.auto_index_limit_per_source,
                    requested_by_clerk_user_id=requested_by_clerk_user_id,
                    mark_featured=False,
                    source_targets=(source,),
                )
                source_success = source_success or bool(result.get("success"))
                source_record_count += int(result.get("record_count", 0))
                source_warning_count += int(result.get("warning_count", 0))
                summaries.append({
                    "source": source,
                    "query": query,
                    "success": result.get("success", False),
                    "record_count": result.get("record_count", 0),
                    "warning_count": result.get("warning_count", 0),
                    "completed_at": _utcnow_iso(),
                    "manual": manual,
                })
            except Exception as exc:
                errors.append(f"{source}:{query}: {exc}")
                source_warning_count += 1
                summaries.append({
                    "source": source,
                    "query": query,
                    "success": False,
                    "record_count": 0,
                    "warning_count": 1,
                    "completed_at": _utcnow_iso(),
                    "manual": manual,
                })

        completed_at = datetime.now(timezone.utc)
        duration_ms = int((completed_at - started_at).total_seconds() * 1000)
        completed_at_iso = completed_at.isoformat()
        job_status["last_completed_at"] = completed_at_iso
        job_status["last_duration_ms"] = duration_ms
        job_status["last_record_count"] = source_record_count
        job_status["last_warning_count"] = source_warning_count
        job_status["total_records_indexed"] += source_record_count
        job_status["total_warning_count"] += source_warning_count
        if not source_success:
            job_status["total_failure_count"] += 1
        job_status["last_error"] = None if source_success else (errors[0] if errors else f"{source_warning_count} warning(s) in last run")

        return {
            "success": source_success,
            "record_count": source_record_count,
            "warning_count": source_warning_count,
            "summaries": summaries,
            "errors": errors,
        }

    def run_source_now(self, source: str, requested_by_clerk_user_id: str = "admin_manual_run") -> dict[str, Any]:
        settings = self._settings
        if not settings:
            from app.config import get_settings
            from app.services.scheduler_config_service import get_runtime_scheduler_settings

            settings = get_runtime_scheduler_settings(get_settings())
            self._settings = settings
            if not self._status.get("source_jobs"):
                self._status["source_jobs"] = self._build_source_job_status(settings)
        intervals = self._effective_source_intervals(settings)
        if source not in intervals:
            raise ValueError(f"Unknown scheduler source: {source}")
        queries = self._queries_for_source(settings, source)
        if not queries:
            raise ValueError(f"No queries configured for source: {source}")
        result = self._run_source_queries(
            settings=settings,
            source=source,
            source_queries=queries,
            requested_by_clerk_user_id=requested_by_clerk_user_id,
            manual=True,
        )
        self._status["last_run_summaries"] = result["summaries"][:50]
        self._status["last_completed_at"] = _utcnow_iso()
        self._status["last_error"] = None if result["success"] else (" | ".join(result["errors"][:20]) if result["errors"] else "manual run completed with warnings")
        if result["success"]:
            self._status["last_success_at"] = self._status["last_completed_at"]
        return {
            "source": source,
            **result,
            "status": self.status(),
        }

    def _shift_minutes(self, minutes: int) -> str:
        return (datetime.now(timezone.utc) + timedelta(minutes=minutes)).isoformat()

    def _parse_dt(self, value: Any) -> datetime | None:
        if not value:
            return None
        text = str(value)
        try:
            if text.isdigit():
                return datetime.fromtimestamp(float(text), tz=timezone.utc)
            return datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError:
            return None


open_access_auto_indexer = OpenAccessAutoIndexer()


def maybe_start_open_access_scheduler(settings: Settings) -> dict[str, Any]:
    if not settings.auto_index_enabled or not settings.has_auto_index_queries:
        return {
            "started": False,
            "reason": "disabled_or_no_queries",
            "status": open_access_auto_indexer.status(),
        }
    open_access_auto_indexer.start(settings)
    return {
        "started": True,
        "status": open_access_auto_indexer.status(),
    }


def restart_open_access_scheduler(settings: Settings) -> dict[str, Any]:
    open_access_auto_indexer.stop()
    return maybe_start_open_access_scheduler(settings)


def stop_open_access_scheduler() -> None:
    open_access_auto_indexer.stop()


def get_open_access_scheduler_status() -> dict[str, Any]:
    return open_access_auto_indexer.status()


def run_open_access_source_now(source: str, requested_by_clerk_user_id: str = "admin_manual_run") -> dict[str, Any]:
    return open_access_auto_indexer.run_source_now(source, requested_by_clerk_user_id=requested_by_clerk_user_id)
