from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel

from app.services.business_ops_service import (
    get_admin_dashboard_overview,
    get_customer_sales_profile,
    get_subscription_plans,
    ingest_stripe_event,
    list_customer_sales_profiles,
    list_team_members,
)
from app.services.local_state_service import (
    build_local_customer_profile,
    build_local_dashboard_overview,
    create_or_update_local_profile,
    fallback_subscription_plans,
    get_local_profile,
    list_local_admin_role_audit_events,
    list_local_profiles,
    log_local_admin_role_audit_event,
    set_local_profile_admin,
)
from app.services.persistence_service import (
    get_profile_by_clerk_user_id,
    list_admin_role_audit_events,
    list_profiles,
    log_admin_role_audit_event,
    update_profile_admin_flag,
)
from app.services.scheduler_service import get_open_access_scheduler_status
from app.services.security_scan_service import get_security_scanner_status, run_security_scan_now
from app.services.admin_auth_service import require_admin
from app.services.scheduler_config_service import (
    get_runtime_scheduler_settings,
    get_scheduler_admin_payload,
    save_scheduler_overrides,
)
from app.config import get_settings
from app.services.scheduler_service import restart_open_access_scheduler
from app.services.scheduler_service import run_open_access_source_now
from app.services.stripe_checkout_service import parse_stripe_webhook_payload, verify_stripe_webhook_signature


router = APIRouter()


def _resolve_profile_summary(clerk_user_id: str) -> dict[str, Any]:
    profile = None
    try:
        profile = get_profile_by_clerk_user_id(clerk_user_id)
    except Exception:
        profile = None
    if not profile:
        profile = get_local_profile(clerk_user_id)
    return {
        "clerk_user_id": clerk_user_id,
        "full_name": (profile or {}).get("full_name"),
        "email": (profile or {}).get("email"),
        "plan": (profile or {}).get("plan"),
    }


class GenericWebhookPayload(BaseModel):
    payload: Dict[str, Any]


class SchedulerConfigPayload(BaseModel):
    auto_index_enabled: bool
    auto_index_pages: int
    auto_index_limit_per_source: int
    auto_index_queries: list[str]
    auto_index_startup_delay_seconds: int
    auto_index_source_intervals: Dict[str, int]
    auto_index_source_queries: Dict[str, list[str]]


class AdminRoleUpdatePayload(BaseModel):
    is_admin: bool


@router.get("/health")
def admin_health():
    return {"status": "admin api ok"}


@router.get("/billing/plans")
def billing_plans():
    try:
        plans = get_subscription_plans()
    except Exception:
        plans = fallback_subscription_plans()
    return jsonable_encoder({"plans": plans})


@router.get("/dashboard/overview")
def dashboard_overview(days: int = 30):
    try:
        return jsonable_encoder(get_admin_dashboard_overview(days))
    except Exception as exc:
        fallback = build_local_dashboard_overview(days)
        fallback["detail"] = f"Supabase analytics unavailable: {exc}"
        return jsonable_encoder(fallback)


@router.get("/dashboard/customers")
def dashboard_customers(limit: int = 25):
    try:
        return jsonable_encoder({
            "customers": list_customer_sales_profiles(limit=max(1, min(limit, 100))),
        })
    except Exception as exc:
        customers = [
            build_local_customer_profile(row["clerk_user_id"])
            for row in list_local_profiles(limit=max(1, min(limit, 100)))
        ]
        return jsonable_encoder({
            "customers": customers,
            "mode": "local_fallback",
            "detail": f"Supabase customers unavailable: {exc}",
        })


@router.get("/dashboard/customers/{clerk_user_id}")
def dashboard_customer_profile(clerk_user_id: str):
    try:
        return jsonable_encoder(get_customer_sales_profile(clerk_user_id))
    except ValueError as exc:
        return jsonable_encoder(build_local_customer_profile(clerk_user_id))
    except Exception as exc:
        payload = build_local_customer_profile(clerk_user_id)
        payload["detail"] = f"Supabase profile unavailable: {exc}"
        return jsonable_encoder(payload)


@router.get("/dashboard/team")
def dashboard_team():
    try:
        members = list_team_members()
        mode = "supabase"
    except Exception:
        members = [
            {
                "full_name": "Senior Data Engineer",
                "role": "Platform Intelligence",
                "department": "Data",
                "status": "planned",
            },
            {
                "full_name": "Senior Data Engineer",
                "role": "Commercial Analytics",
                "department": "Data",
                "status": "planned",
            },
        ]
        mode = "local_fallback"
    return jsonable_encoder({
        "team_members": members,
        "mode": mode,
    })


@router.get("/jobs/status")
def jobs_status(_: dict = Depends(require_admin)):
    return jsonable_encoder({
        "open_access_auto_indexer": get_open_access_scheduler_status(),
        "security_auto_scanner": get_security_scanner_status(),
    })


@router.get("/jobs/config")
def jobs_config(_: dict = Depends(require_admin)):
    return jsonable_encoder(get_scheduler_admin_payload(get_settings()))


@router.post("/jobs/config")
def update_jobs_config(payload: SchedulerConfigPayload, admin_identity: dict = Depends(require_admin)):
    overrides = save_scheduler_overrides(
        payload.model_dump(),
        updated_by_clerk_user_id=admin_identity.get("clerk_user_id"),
    )
    runtime_settings = get_runtime_scheduler_settings(get_settings())
    restart = restart_open_access_scheduler(runtime_settings)
    return jsonable_encoder({
        "success": True,
        "overrides": overrides,
        "effective": get_scheduler_admin_payload(get_settings())["effective"],
        "restart": restart,
        "admin_identity": {
            "clerk_user_id": admin_identity.get("clerk_user_id"),
            "source": admin_identity.get("source"),
        },
    })


@router.post("/jobs/run-source/{source}")
def run_jobs_source_now(source: str, admin_identity: dict = Depends(require_admin)):
    try:
        result = run_open_access_source_now(
            source,
            requested_by_clerk_user_id=admin_identity.get("clerk_user_id") or "admin_manual_run",
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Manual source run failed: {exc}") from exc

    return jsonable_encoder({
        "success": True,
        "result": result,
    })


@router.post("/security/run")
def run_security_scan(admin_identity: dict = Depends(require_admin)):
    result = run_security_scan_now(
        requested_by=admin_identity.get("clerk_user_id") or "admin_manual_run",
    )
    return jsonable_encoder({
        "success": True,
        "result": result,
    })


@router.get("/roles/users")
def list_role_managed_users(
    limit: int = 50,
    search: str = "",
    _: dict = Depends(require_admin),
):
    safe_limit = max(1, min(limit, 200))
    try:
        rows = list_profiles(limit=safe_limit, search=search)
        mode = "supabase"
    except Exception:
        rows = list_local_profiles(limit=safe_limit)
        if search.strip():
            needle = search.strip().lower()
            rows = [
                row for row in rows
                if needle in str(row.get("clerk_user_id", "")).lower()
                or needle in str(row.get("email", "")).lower()
                or needle in str(row.get("full_name", "")).lower()
            ]
        mode = "local_fallback"

    settings = get_settings()
    users = []
    for row in rows:
        clerk_user_id = row.get("clerk_user_id") or ""
        users.append({
            "clerk_user_id": clerk_user_id,
            "email": row.get("email"),
            "full_name": row.get("full_name"),
            "plan": row.get("plan", "free"),
            "is_admin": bool(row.get("is_admin")),
            "admin_source": "env_allowlist" if clerk_user_id in settings.admin_clerk_user_ids else ("profile_flag" if row.get("is_admin") else "none"),
            "updated_at": row.get("updated_at"),
        })

    return jsonable_encoder({
        "users": users,
        "mode": mode,
        "search": search,
    })


@router.post("/roles/users/{clerk_user_id}")
def update_role_managed_user(
    clerk_user_id: str,
    payload: AdminRoleUpdatePayload,
    admin_identity: dict = Depends(require_admin),
):
    settings = get_settings()
    previous_profile = None
    try:
        previous_profile = get_profile_by_clerk_user_id(clerk_user_id)
    except Exception:
        previous_profile = None
    if not previous_profile:
        previous_profile = get_local_profile(clerk_user_id)
    previous_is_admin = bool((previous_profile or {}).get("is_admin"))

    if (
        clerk_user_id == admin_identity.get("clerk_user_id")
        and not payload.is_admin
        and clerk_user_id not in settings.admin_clerk_user_ids
    ):
        raise HTTPException(
            status_code=400,
            detail="You cannot remove your own last profile-based admin grant.",
        )

    try:
        profile = update_profile_admin_flag(clerk_user_id, payload.is_admin)
        mode = "supabase"
    except ValueError:
        fallback_profile = get_local_profile(clerk_user_id)
        if not fallback_profile:
            fallback_profile = create_or_update_local_profile({
                "clerk_user_id": clerk_user_id,
                "full_name": clerk_user_id.replace("_", " ").title(),
                "plan": "free",
            })
        profile = set_local_profile_admin(clerk_user_id, payload.is_admin)
        mode = "local_fallback"
    except Exception:
        fallback_profile = get_local_profile(clerk_user_id)
        if not fallback_profile:
            fallback_profile = create_or_update_local_profile({
                "clerk_user_id": clerk_user_id,
                "full_name": clerk_user_id.replace("_", " ").title(),
                "plan": "free",
            })
        profile = set_local_profile_admin(clerk_user_id, payload.is_admin)
        mode = "local_fallback"

    admin_source = "env_allowlist" if clerk_user_id in settings.admin_clerk_user_ids else ("profile_flag" if payload.is_admin else "none")
    audit_payload = {
        "actor_clerk_user_id": admin_identity.get("clerk_user_id"),
        "target_clerk_user_id": clerk_user_id,
        "action": "grant_admin" if payload.is_admin else "revoke_admin",
        "admin_source": admin_source,
        "previous_is_admin": previous_is_admin,
        "new_is_admin": bool(payload.is_admin),
        "metadata": {
            "actor_source": admin_identity.get("source"),
            "persistence_mode": mode,
            "target_email": profile.get("email"),
            "target_full_name": profile.get("full_name"),
            "target_plan": profile.get("plan", "free"),
        },
    }
    try:
        log_admin_role_audit_event(audit_payload)
    except Exception:
        log_local_admin_role_audit_event(audit_payload)

    return jsonable_encoder({
        "success": True,
        "profile": {
            "clerk_user_id": profile.get("clerk_user_id"),
            "email": profile.get("email"),
            "full_name": profile.get("full_name"),
            "plan": profile.get("plan", "free"),
            "is_admin": bool(profile.get("is_admin")),
            "updated_at": profile.get("updated_at"),
        },
        "mode": mode,
        "admin_source": admin_source,
    })


@router.get("/roles/audit")
def admin_role_audit(
    limit: int = 50,
    _: dict = Depends(require_admin),
):
    safe_limit = max(1, min(limit, 200))
    try:
        rows = list_admin_role_audit_events(limit=safe_limit)
        mode = "supabase"
    except Exception:
        rows = list_local_admin_role_audit_events(limit=safe_limit)
        mode = "local_fallback"

    enriched = []
    for row in rows:
        actor_id = row.get("actor_clerk_user_id") or ""
        target_id = row.get("target_clerk_user_id") or ""
        enriched.append({
            **row,
            "actor": _resolve_profile_summary(actor_id) if actor_id else None,
            "target": _resolve_profile_summary(target_id) if target_id else None,
        })

    return jsonable_encoder({
        "events": enriched,
        "mode": mode,
    })


@router.post("/webhooks/clerk")
def admin_clerk_webhook(payload: Dict[str, Any]):
    raise HTTPException(
        status_code=503,
        detail="Clerk webhook ingestion is disabled until signature verification is configured.",
    )


@router.post("/webhooks/stripe")
async def admin_stripe_webhook(request: Request):
    try:
        raw_body = await request.body()
        signature = request.headers.get("stripe-signature")
        if not verify_stripe_webhook_signature(raw_body, signature):
            raise HTTPException(status_code=400, detail="Invalid Stripe webhook signature.")
        payload = parse_stripe_webhook_payload(raw_body)
        return jsonable_encoder(ingest_stripe_event(payload))
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to process Stripe event: {exc}") from exc
