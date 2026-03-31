from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
import re
import threading
from typing import Any

from app.config import Settings


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _utcnow_iso() -> str:
    return _utcnow().isoformat()


@dataclass(frozen=True)
class ScanRule:
    key: str
    severity: str
    title: str
    file_path: str
    pattern: re.Pattern[str]
    detail: str


SCAN_RULES: tuple[ScanRule, ...] = (
    ScanRule(
        key="product_fetch_without_auth",
        severity="critical",
        title="Protected product route called without authenticated fetch",
        file_path="app/static/js/app.js",
        pattern=re.compile(r"fetch\((\"|`)\/product\/"),
        detail="Protected product routes should use authenticatedFetch or guardedProductFetch.",
    ),
    ScanRule(
        key="js_readable_clerk_session_cookie",
        severity="critical",
        title="JS-readable Clerk session token handling detected",
        file_path="app/static/js/app.js",
        pattern=re.compile(r"frip_clerk_session|document\.cookie"),
        detail="Session tokens should not be persisted in JS-readable cookies.",
    ),
    ScanRule(
        key="latest_clerk_asset",
        severity="high",
        title="Unpinned Clerk browser asset detected",
        file_path="app/templates/base.html",
        pattern=re.compile(r"@latest"),
        detail="Pin the Clerk browser asset to a specific version.",
    ),
    ScanRule(
        key="auth_profile_local_storage",
        severity="high",
        title="Sensitive auth or billing profile stored in localStorage",
        file_path="app/static/js/app.js",
        pattern=re.compile(r'localStorage\.setItem\("frip_auth_profile"|localStorage\.setItem\("billing'),
        detail="Onboarding and billing-intent fields should stay out of long-lived localStorage.",
    ),
    ScanRule(
        key="hardcoded_publishable_key",
        severity="high",
        title="Hardcoded Stripe or Clerk key detected",
        file_path="app",
        pattern=re.compile(r"(pk_(test|live)_[A-Za-z0-9]+|sk_(test|live)_[A-Za-z0-9]+)"),
        detail="Keys should come from environment variables, not source files.",
    ),
)


class SecurityAutoScanner:
    def __init__(self) -> None:
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()
        self._started = False
        self._settings: Settings | None = None
        self._status: dict[str, Any] = {
            "running": False,
            "enabled": False,
            "started_at": None,
            "last_started_at": None,
            "last_completed_at": None,
            "last_success_at": None,
            "last_error": None,
            "last_duration_ms": None,
            "last_findings": [],
            "last_summary": {},
            "total_runs": 0,
            "total_findings": 0,
            "next_due_at": None,
        }

    def start(self, settings: Settings) -> None:
        with self._lock:
            if self._started:
                return
            self._settings = settings
            self._stop_event.clear()
            self._thread = threading.Thread(
                target=self._run_loop,
                name="security-auto-scanner",
                daemon=True,
            )
            self._started = True
            self._status["running"] = True
            self._status["enabled"] = bool(settings.security_scan_enabled)
            self._status["started_at"] = _utcnow_iso()
            self._status["next_due_at"] = _utcnow_iso()
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
                "enabled": bool(settings and settings.security_scan_enabled),
                "interval_hours": settings.security_scan_interval_hours if settings else None,
            }

    def run_now(self, requested_by: str = "admin_manual_run") -> dict[str, Any]:
        settings = self._settings
        if not settings:
            from app.config import get_settings
            settings = get_settings()
            self._settings = settings
        return self._run_scan(requested_by=requested_by, manual=True)

    def _run_loop(self) -> None:
        settings = self._settings
        if not settings or not settings.security_scan_enabled:
            return
        if settings.security_scan_startup_delay_seconds:
            if self._stop_event.wait(settings.security_scan_startup_delay_seconds):
                return
        while not self._stop_event.is_set():
            self._run_scan(requested_by="system_security_scanner", manual=False)
            next_wait_seconds = max(3600, settings.security_scan_interval_hours * 3600)
            if self._stop_event.wait(next_wait_seconds):
                break

    def _run_scan(self, requested_by: str, manual: bool) -> dict[str, Any]:
        started_at = _utcnow()
        started_at_iso = started_at.isoformat()
        findings: list[dict[str, Any]] = []
        severity_totals = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        last_error = None

        self._status["last_started_at"] = started_at_iso
        self._status["total_runs"] += 1

        try:
            for rule in SCAN_RULES:
                findings.extend(self._apply_rule(rule))
            findings.extend(self._scan_clerk_webhook_route())
        except Exception as exc:
            last_error = str(exc)

        for finding in findings:
            severity = finding.get("severity", "low")
            severity_totals[severity] = severity_totals.get(severity, 0) + 1

        completed_at = _utcnow()
        duration_ms = int((completed_at - started_at).total_seconds() * 1000)
        completed_at_iso = completed_at.isoformat()
        self._status["last_completed_at"] = completed_at_iso
        self._status["last_duration_ms"] = duration_ms
        self._status["last_findings"] = findings[:100]
        self._status["last_summary"] = {
            "requested_by": requested_by,
            "manual": manual,
            "total_findings": len(findings),
            "severity_totals": severity_totals,
        }
        self._status["total_findings"] += len(findings)
        self._status["last_error"] = last_error
        self._status["next_due_at"] = (
            completed_at + timedelta(hours=max(1, (self._settings or Settings()).security_scan_interval_hours))
        ).isoformat()
        if last_error is None:
            self._status["last_success_at"] = completed_at_iso

        return self.status()

    def _apply_rule(self, rule: ScanRule) -> list[dict[str, Any]]:
        matches: list[dict[str, Any]] = []
        if rule.file_path == "app":
            for path in PROJECT_ROOT.glob("app/**/*.py"):
                matches.extend(self._scan_file(rule, path))
            for path in PROJECT_ROOT.glob("app/**/*.html"):
                matches.extend(self._scan_file(rule, path))
            for path in PROJECT_ROOT.glob("app/**/*.js"):
                matches.extend(self._scan_file(rule, path))
            return matches

        path = PROJECT_ROOT / rule.file_path
        return self._scan_file(rule, path)

    def _scan_file(self, rule: ScanRule, path: Path) -> list[dict[str, Any]]:
        if not path.exists() or not path.is_file():
            return []
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except Exception:
            return []

        results: list[dict[str, Any]] = []
        for line_number, line in enumerate(lines, start=1):
            if not rule.pattern.search(line):
                continue
            if rule.key == "product_fetch_without_auth" and "guardedProductFetch(" in line:
                continue
            results.append({
                "rule": rule.key,
                "severity": rule.severity,
                "title": rule.title,
                "detail": rule.detail,
                "file_path": str(path.relative_to(PROJECT_ROOT)),
                "line": line_number,
                "snippet": line.strip()[:300],
            })
        return results

    def _scan_clerk_webhook_route(self) -> list[dict[str, Any]]:
        path = PROJECT_ROOT / "app/api/admin.py"
        if not path.exists():
            return []
        content = path.read_text(encoding="utf-8")
        if "Clerk webhook ingestion is disabled until signature verification is configured." in content:
            return []
        if "@router.post(\"/webhooks/clerk\")" not in content:
            return []
        return [{
            "rule": "clerk_webhook_unverified",
            "severity": "high",
            "title": "Clerk webhook route is enabled without enforced verification",
            "detail": "Disable the route or add signature verification before accepting Clerk webhook traffic.",
            "file_path": "app/api/admin.py",
            "line": next(
                (index for index, line in enumerate(content.splitlines(), start=1) if '@router.post("/webhooks/clerk")' in line),
                1,
            ),
            "snippet": '@router.post("/webhooks/clerk")',
        }]


security_auto_scanner = SecurityAutoScanner()


def maybe_start_security_scanner(settings: Settings) -> dict[str, Any]:
    if not settings.security_scan_enabled:
        return {
            "started": False,
            "reason": "disabled",
            "status": security_auto_scanner.status(),
        }
    security_auto_scanner.start(settings)
    return {
        "started": True,
        "status": security_auto_scanner.status(),
    }


def stop_security_scanner() -> None:
    security_auto_scanner.stop()


def get_security_scanner_status() -> dict[str, Any]:
    return security_auto_scanner.status()


def run_security_scan_now(requested_by: str = "admin_manual_run") -> dict[str, Any]:
    return security_auto_scanner.run_now(requested_by=requested_by)
