from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True)
class PlanDefinition:
    code: str
    name: str
    price: str
    tagline: str
    description: str


PLANS: tuple[PlanDefinition, ...] = (
    PlanDefinition(
        code="free",
        name="Free",
        price="$0",
        tagline="Start curious",
        description="Search, open, and pressure-test the workflow before you commit.",
    ),
    PlanDefinition(
        code="student",
        name="Student",
        price="$2.99/mo",
        tagline="Late-night study weapon",
        description="Made for focused students who want stronger search, summaries, and uploads.",
    ),
    PlanDefinition(
        code="pro",
        name="Pro",
        price="$9.99/mo",
        tagline="Breakfast with brains",
        description="For daily researchers who want speed, headroom, and sharper workspace tooling.",
    ),
    PlanDefinition(
        code="enterprise",
        name="Enterprise",
        price="$14.99/mo",
        tagline="Dinner with Da Vinci energy",
        description="For teams, labs, and operators who need commercial visibility and collaboration next.",
    ),
)

PLAN_MAP = {plan.code: plan for plan in PLANS}


@dataclass(frozen=True)
class Settings:
    app_name: str = "Frontier Research Intelligence Platform"
    clerk_publishable_key: str = ""
    clerk_js_version: str = "5.56.0"
    clerk_secret_key: str = ""
    clerk_jwks_json: str = ""
    clerk_jwt_public_key: str = ""
    clerk_jwt_issuer: str = ""
    clerk_jwt_audiences: tuple[str, ...] = ()
    clerk_authorized_parties: tuple[str, ...] = ()
    clerk_jwt_leeway_seconds: int = 10
    supabase_url: str = ""
    supabase_anon_key: str = ""
    app_base_url: str = "http://localhost:8000"
    stripe_publishable_key: str = ""
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_price_ids: dict[str, str] | None = None
    auto_index_enabled: bool = False
    auto_index_interval_minutes: int = 360
    auto_index_pages: int = 2
    auto_index_limit_per_source: int = 25
    auto_index_queries: tuple[str, ...] = ()
    auto_index_startup_delay_seconds: int = 30
    auto_index_source_intervals: dict[str, int] | None = None
    auto_index_source_queries: dict[str, tuple[str, ...]] | None = None
    security_scan_enabled: bool = False
    security_scan_interval_hours: int = 24
    security_scan_startup_delay_seconds: int = 60
    admin_clerk_user_ids: tuple[str, ...] = ()

    @property
    def has_clerk(self) -> bool:
        return bool(self.clerk_publishable_key)

    @property
    def has_clerk_verification(self) -> bool:
        return bool(self.clerk_jwks_json or self.clerk_jwt_public_key or self.clerk_secret_key)

    @property
    def has_supabase(self) -> bool:
        return bool(self.supabase_url)

    @property
    def has_stripe(self) -> bool:
        return bool(self.stripe_publishable_key and self.stripe_secret_key)

    @property
    def has_auto_index_queries(self) -> bool:
        return bool(self.auto_index_queries) or bool(self.auto_index_source_queries)

    @property
    def has_auto_index_source_intervals(self) -> bool:
        return bool(self.auto_index_source_intervals)

    @property
    def has_auto_index_source_queries(self) -> bool:
        return bool(self.auto_index_source_queries)


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int, minimum: int = 1, maximum: int = 100000) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        parsed = int(value)
    except ValueError:
        return default
    return max(minimum, min(parsed, maximum))


def _env_list(name: str) -> tuple[str, ...]:
    raw = os.getenv(name, "")
    items = tuple(item.strip() for item in raw.split(",") if item.strip())
    return items


def _env_interval_map(name: str) -> dict[str, int]:
    raw = os.getenv(name, "")
    pairs: dict[str, int] = {}
    for part in raw.split(","):
        item = part.strip()
        if not item or ":" not in item:
            continue
        key, value = item.split(":", 1)
        key = key.strip()
        try:
            minutes = int(value.strip())
        except ValueError:
            continue
        if key:
            pairs[key] = max(5, min(minutes, 10080))
    return pairs


def _env_source_query_map(name: str) -> dict[str, tuple[str, ...]]:
    raw = os.getenv(name, "")
    groups: dict[str, tuple[str, ...]] = {}
    for chunk in raw.split(";"):
        item = chunk.strip()
        if not item or "=" not in item:
            continue
        key, value = item.split("=", 1)
        source = key.strip()
        queries = tuple(part.strip() for part in value.split("|") if part.strip())
        if source and queries:
            groups[source] = queries
    return groups


@lru_cache
def get_settings() -> Settings:
    return Settings(
        clerk_publishable_key=(
            os.getenv("CLERK_PUBLISHABLE_KEY")
            or os.getenv("NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY")
            or ""
        ),
        clerk_js_version=os.getenv("CLERK_JS_VERSION", "5.56.0"),
        clerk_secret_key=os.getenv("CLERK_SECRET_KEY", ""),
        clerk_jwks_json=os.getenv("CLERK_JWKS_JSON", ""),
        clerk_jwt_public_key=os.getenv("CLERK_JWT_PUBLIC_KEY", ""),
        clerk_jwt_issuer=os.getenv("CLERK_JWT_ISSUER", ""),
        clerk_jwt_audiences=_env_list("CLERK_JWT_AUDIENCES"),
        clerk_authorized_parties=_env_list("CLERK_AUTHORIZED_PARTIES"),
        clerk_jwt_leeway_seconds=_env_int("CLERK_JWT_LEEWAY_SECONDS", 10, minimum=0, maximum=300),
        supabase_url=os.getenv("SUPABASE_URL", ""),
        supabase_anon_key=os.getenv("SUPABASE_ANON_KEY", ""),
        app_base_url=os.getenv("APP_BASE_URL", "http://localhost:8000"),
        stripe_publishable_key=os.getenv("STRIPE_PUBLISHABLE_KEY", ""),
        stripe_secret_key=os.getenv("STRIPE_SECRET_KEY", ""),
        stripe_webhook_secret=os.getenv("STRIPE_WEBHOOK_SECRET", ""),
        stripe_price_ids={
            "student": os.getenv("STRIPE_PRICE_ID_STUDENT", ""),
            "pro": os.getenv("STRIPE_PRICE_ID_PRO", ""),
            "enterprise": os.getenv("STRIPE_PRICE_ID_ENTERPRISE", ""),
        },
        auto_index_enabled=_env_bool("OPEN_ACCESS_AUTO_INDEX_ENABLED", False),
        auto_index_interval_minutes=_env_int("OPEN_ACCESS_AUTO_INDEX_INTERVAL_MINUTES", 360, minimum=5, maximum=10080),
        auto_index_pages=_env_int("OPEN_ACCESS_AUTO_INDEX_PAGES", 2, minimum=1, maximum=20),
        auto_index_limit_per_source=_env_int("OPEN_ACCESS_AUTO_INDEX_LIMIT_PER_SOURCE", 25, minimum=1, maximum=100),
        auto_index_queries=_env_list("OPEN_ACCESS_AUTO_INDEX_QUERIES"),
        auto_index_startup_delay_seconds=_env_int("OPEN_ACCESS_AUTO_INDEX_STARTUP_DELAY_SECONDS", 30, minimum=0, maximum=3600),
        auto_index_source_intervals=_env_interval_map("OPEN_ACCESS_AUTO_INDEX_SOURCE_INTERVALS"),
        auto_index_source_queries=_env_source_query_map("OPEN_ACCESS_AUTO_INDEX_SOURCE_QUERIES"),
        security_scan_enabled=_env_bool("SECURITY_SCAN_ENABLED", False),
        security_scan_interval_hours=_env_int("SECURITY_SCAN_INTERVAL_HOURS", 24, minimum=1, maximum=168),
        security_scan_startup_delay_seconds=_env_int("SECURITY_SCAN_STARTUP_DELAY_SECONDS", 60, minimum=0, maximum=3600),
        admin_clerk_user_ids=_env_list("ADMIN_CLERK_USER_IDS"),
    )
