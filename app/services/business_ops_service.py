from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from app.services.persistence_service import (
    create_or_update_profile,
    get_profile_by_clerk_user_id,
)
from app.services.supabase_service import get_supabase


DAILY_COUNTERS: Dict[str, str] = {
    "search": "search_count",
    "view": "view_count",
    "save": "save_count",
    "question": "question_count",
    "compare": "compare_count",
    "upload": "upload_count",
}

SALES_COUNTERS: Dict[str, str] = {
    "search": "total_searches",
    "view": "total_views",
    "compare": "total_comparisons",
    "question": "total_questions",
    "upload": "total_uploads",
}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _iso_to_datetime(value: Any) -> Optional[datetime]:
    if not value:
        return None
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc) if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, tz=timezone.utc)
    text = str(value).strip()
    if not text:
        return None
    text = text.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    return parsed.astimezone(timezone.utc) if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _date_from_event(event_row: Dict[str, Any]) -> date:
    created_at = _iso_to_datetime(event_row.get("created_at"))
    return (created_at or _utcnow()).date()


def _clean_text(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _truncate_text(value: Any, limit: int = 240) -> Optional[str]:
    text = _clean_text(value)
    if not text:
        return None
    return text[:limit]


def _get_profile_by_id(profile_id: str) -> Optional[Dict[str, Any]]:
    res = (
        get_supabase()
        .table("profiles")
        .select("*")
        .eq("id", profile_id)
        .limit(1)
        .execute()
    )
    return res.data[0] if res.data else None


def _get_customer_for_profile(profile_id: str) -> Optional[Dict[str, Any]]:
    res = (
        get_supabase()
        .table("billing_customers")
        .select("*")
        .eq("profile_id", profile_id)
        .limit(1)
        .execute()
    )
    return res.data[0] if res.data else None


def _get_customer_for_stripe_id(stripe_customer_id: Optional[str]) -> Optional[Dict[str, Any]]:
    if not stripe_customer_id:
        return None
    res = (
        get_supabase()
        .table("billing_customers")
        .select("*")
        .eq("stripe_customer_id", stripe_customer_id)
        .limit(1)
        .execute()
    )
    return res.data[0] if res.data else None


def _get_profile_by_email(email: Optional[str]) -> Optional[Dict[str, Any]]:
    email = _clean_text(email)
    if not email:
        return None
    res = (
        get_supabase()
        .table("profiles")
        .select("*")
        .eq("email", email)
        .limit(1)
        .execute()
    )
    return res.data[0] if res.data else None


def _merge_dicts(existing: Any, updates: Any) -> Dict[str, Any]:
    merged: Dict[str, Any] = {}
    if isinstance(existing, dict):
        merged.update(existing)
    if isinstance(updates, dict):
        merged.update(updates)
    return merged


def _safe_list(value: Any) -> List[Any]:
    return value if isinstance(value, list) else []


def _topic_with_weight(entries: List[Any], topic: Optional[str], delta: float) -> List[Dict[str, Any]]:
    counts: Dict[str, float] = {}
    for item in entries:
        if isinstance(item, dict):
            name = _clean_text(item.get("topic"))
            weight = float(item.get("score") or 0)
        else:
            name = _clean_text(item)
            weight = 1.0
        if name:
            counts[name] = counts.get(name, 0) + weight

    normalized_topic = _clean_text(topic)
    if normalized_topic:
        counts[normalized_topic] = counts.get(normalized_topic, 0) + delta

    ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    return [{"topic": name, "score": round(score, 2)} for name, score in ranked[:5]]


def _recent_activity(entries: List[Any], event_row: Dict[str, Any]) -> List[Dict[str, Any]]:
    clean_entries: List[Dict[str, Any]] = []
    for item in entries:
        if isinstance(item, dict):
            clean_entries.append({
                "created_at": item.get("created_at"),
                "event_type": item.get("event_type"),
                "title": item.get("title"),
                "topic": item.get("topic"),
            })
    clean_entries.insert(0, {
        "created_at": (_iso_to_datetime(event_row.get("created_at")) or _utcnow()).isoformat(),
        "event_type": event_row.get("event_type"),
        "title": _truncate_text(event_row.get("title")),
        "topic": _truncate_text(event_row.get("topic"), 120),
    })
    return clean_entries[:10]


def _best_fit_upgrade_plan(current_plan: str, usage_totals: Dict[str, int]) -> Optional[str]:
    if current_plan == "free":
        if usage_totals.get("total_searches", 0) >= 30 or usage_totals.get("total_uploads", 0) >= 2:
            return "student"
        return None
    if current_plan == "student":
        if usage_totals.get("total_searches", 0) >= 120 or usage_totals.get("total_questions", 0) >= 15:
            return "pro"
        return None
    if current_plan == "pro":
        if usage_totals.get("total_searches", 0) >= 450 or usage_totals.get("total_comparisons", 0) >= 30:
            return "enterprise"
        return None
    return None


def _engagement_status(last_seen_at: Optional[datetime]) -> str:
    if not last_seen_at:
        return "new"
    age_days = (_utcnow() - last_seen_at).days
    if age_days <= 3:
        return "power"
    if age_days <= 14:
        return "active"
    if age_days <= 30:
        return "cooling"
    return "at_risk"


def _calculate_upgrade_score(current_plan: str, usage_totals: Dict[str, int], total_revenue_cents: int) -> float:
    score = 0.0
    score += min(usage_totals.get("total_searches", 0) / 3, 35)
    score += min(usage_totals.get("total_views", 0) / 4, 20)
    score += min(usage_totals.get("total_questions", 0) * 2.5, 20)
    score += min(usage_totals.get("total_comparisons", 0) * 2.0, 15)
    if current_plan == "free" and total_revenue_cents == 0:
        score += 10
    if current_plan in {"student", "pro"}:
        score += 5
    return round(min(score, 100.0), 2)


def _calculate_churn_risk(last_seen_at: Optional[datetime], payment_failures: int) -> float:
    score = float(payment_failures * 18)
    if last_seen_at:
        age_days = (_utcnow() - last_seen_at).days
        if age_days > 7:
            score += min((age_days - 7) * 1.5, 55)
    return round(min(score, 100.0), 2)


def _calculate_health_score(upgrade_score: float, churn_risk: float, total_revenue_cents: int) -> float:
    revenue_bonus = min(total_revenue_cents / 1000, 20)
    score = 55 + (upgrade_score * 0.2) + revenue_bonus - (churn_risk * 0.45)
    return round(max(0.0, min(score, 100.0)), 2)


def _lifecycle_stage(plan_code: str, total_orders: int, total_activity: int) -> str:
    if total_orders > 0 and plan_code != "free":
        return "customer"
    if total_activity >= 20:
        return "product_qualified"
    if total_activity > 0:
        return "activated"
    return "lead"


def _next_best_actions(plan_code: str, upgrade_plan: Optional[str], churn_risk: float, engagement_status: str) -> List[str]:
    actions: List[str] = []
    if plan_code == "free":
        actions.append("Trigger an activation campaign around saved searches and AI summaries.")
    if upgrade_plan:
        actions.append(f"Recommend an upgrade path from {plan_code} to {upgrade_plan}.")
    if churn_risk >= 40:
        actions.append("Queue a retention outreach with a usage recap and support offer.")
    if engagement_status == "power":
        actions.append("Invite this account to premium workflow features or team expansion.")
    return actions[:4]


def get_subscription_plans() -> List[Dict[str, Any]]:
    res = (
        get_supabase()
        .table("subscription_plans")
        .select("*")
        .eq("is_active", True)
        .order("price_monthly_cents")
        .execute()
    )
    return res.data or []


def ensure_billing_customer_for_profile(
    profile: Dict[str, Any],
    acquisition_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    sb = get_supabase()
    existing = _get_customer_for_profile(profile["id"])
    current = existing.copy() if existing else {}
    acquisition_context = acquisition_context or {}
    plan_code = _clean_text(profile.get("plan")) or _clean_text(current.get("plan_code")) or "free"

    row = {
        "profile_id": profile["id"],
        "clerk_user_id": profile.get("clerk_user_id"),
        "email": profile.get("email"),
        "full_name": profile.get("full_name"),
        "plan_code": plan_code,
        "sales_segment": "team" if plan_code == "enterprise" else "self_serve",
        "acquisition_channel": _clean_text(acquisition_context.get("acquisition_channel")) or current.get("acquisition_channel"),
        "marketing_campaign": _clean_text(acquisition_context.get("marketing_campaign")) or current.get("marketing_campaign"),
        "conversion_source": _clean_text(acquisition_context.get("conversion_source")) or current.get("conversion_source"),
        "lifecycle_stage": current.get("lifecycle_stage") or ("customer" if plan_code != "free" else "lead"),
        "metadata": _merge_dicts(current.get("metadata"), acquisition_context.get("metadata")),
    }
    res = sb.table("billing_customers").upsert(row, on_conflict="profile_id").execute()
    return res.data[0]


def sync_profile_to_business_records(
    profile: Dict[str, Any],
    acquisition_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    customer = ensure_billing_customer_for_profile(profile, acquisition_context=acquisition_context)
    sales_profile = refresh_customer_sales_profile(profile["id"])
    return {
        "customer": customer,
        "sales_profile": sales_profile,
    }


def refresh_customer_sales_profile(profile_id: str) -> Dict[str, Any]:
    sb = get_supabase()
    profile = _get_profile_by_id(profile_id)
    if not profile:
        raise ValueError("Profile not found")

    customer = ensure_billing_customer_for_profile(profile)

    usage_rows = (
        sb.table("profile_usage_daily")
        .select("*")
        .eq("profile_id", profile_id)
        .order("usage_date", desc=True)
        .limit(90)
        .execute()
        .data
        or []
    )
    transactions = (
        sb.table("billing_transactions")
        .select("*")
        .eq("profile_id", profile_id)
        .order("collected_at", desc=True)
        .limit(200)
        .execute()
        .data
        or []
    )
    subscriptions = (
        sb.table("billing_subscriptions")
        .select("*")
        .eq("profile_id", profile_id)
        .order("updated_at", desc=True)
        .limit(20)
        .execute()
        .data
        or []
    )
    topic_rows = (
        sb.table("profile_topic_interests")
        .select("topic,recommendation_score,last_interaction_at")
        .eq("profile_id", profile_id)
        .order("recommendation_score", desc=True)
        .limit(5)
        .execute()
        .data
        or []
    )
    recent_events = (
        sb.table("paper_activity_events")
        .select("created_at,event_type,title,topic")
        .eq("profile_id", profile_id)
        .order("created_at", desc=True)
        .limit(8)
        .execute()
        .data
        or []
    )

    totals = {
        "total_searches": sum(int(row.get("search_count") or 0) for row in usage_rows),
        "total_views": sum(int(row.get("view_count") or 0) for row in usage_rows),
        "total_comparisons": sum(int(row.get("compare_count") or 0) for row in usage_rows),
        "total_questions": sum(int(row.get("question_count") or 0) for row in usage_rows),
        "total_uploads": sum(int(row.get("upload_count") or 0) for row in usage_rows),
    }
    total_activity = sum(int(row.get("event_count") or 0) for row in usage_rows)
    total_revenue_cents = sum(
        int(row.get("amount_total_cents") or 0)
        for row in transactions
        if row.get("status") in {"paid", "succeeded", "complete"}
    )
    total_orders = sum(
        1
        for row in transactions
        if row.get("status") in {"paid", "succeeded", "complete"}
    )
    payment_failures = sum(1 for row in transactions if row.get("status") in {"failed", "payment_failed"})

    latest_subscription = next(
        (row for row in subscriptions if row.get("status") in {"active", "trialing", "past_due", "incomplete"}),
        subscriptions[0] if subscriptions else None,
    )
    plan_code = (
        _clean_text(customer.get("plan_code"))
        or _clean_text((latest_subscription or {}).get("plan_code"))
        or _clean_text(profile.get("plan"))
        or "free"
    )
    monthly_recurring_cents = int((latest_subscription or {}).get("unit_amount_cents") or 0)
    last_seen_at = max(
        (_iso_to_datetime(row.get("last_event_at")) for row in usage_rows if row.get("last_event_at")),
        default=None,
    )
    first_value_at = min(
        (_iso_to_datetime(row.get("collected_at")) for row in transactions if row.get("collected_at") and row.get("status") in {"paid", "succeeded", "complete"}),
        default=None,
    )

    upgrade_plan = _best_fit_upgrade_plan(plan_code, totals)
    upgrade_score = _calculate_upgrade_score(plan_code, totals, total_revenue_cents)
    churn_risk = _calculate_churn_risk(last_seen_at, payment_failures)
    health_score = _calculate_health_score(upgrade_score, churn_risk, total_revenue_cents)
    lifecycle_stage = _lifecycle_stage(plan_code, total_orders, total_activity)
    engagement_status = _engagement_status(last_seen_at)

    top_topics = [
        {
            "topic": row.get("topic"),
            "score": round(float(row.get("recommendation_score") or 0), 2),
            "last_interaction_at": row.get("last_interaction_at"),
        }
        for row in topic_rows
        if row.get("topic")
    ]
    product_fit_summary = (
        f"{profile.get('full_name') or profile.get('email') or 'This account'} is on the {plan_code} tier with "
        f"{totals['total_searches']} searches, {totals['total_views']} views, and {total_orders} completed orders."
    )
    next_actions = _next_best_actions(plan_code, upgrade_plan, churn_risk, engagement_status)

    sales_row = {
        "profile_id": profile_id,
        "billing_customer_id": customer.get("id"),
        "current_plan_code": plan_code,
        "lifecycle_stage": lifecycle_stage,
        "engagement_status": engagement_status,
        "revenue_band": "paid" if total_revenue_cents > 0 else "prepaid",
        "buyer_persona": "team" if plan_code == "enterprise" else "researcher",
        "best_fit_upgrade_plan": upgrade_plan,
        "upgrade_reason": "Usage intensity exceeds the current tier comfort zone." if upgrade_plan else None,
        "upgrade_propensity_score": upgrade_score,
        "churn_risk_score": churn_risk,
        "health_score": health_score,
        "acquisition_channel": customer.get("acquisition_channel"),
        "product_fit_summary": product_fit_summary,
        "top_topics": top_topics,
        "recent_activity": recent_events,
        "next_best_actions": next_actions,
        "last_seen_at": last_seen_at.isoformat() if last_seen_at else None,
        "first_value_at": first_value_at.isoformat() if first_value_at else None,
        "total_revenue_cents": total_revenue_cents,
        "monthly_recurring_revenue_cents": monthly_recurring_cents,
        "total_orders": total_orders,
        **totals,
        "metadata": {
            "latest_subscription_status": (latest_subscription or {}).get("status"),
            "payment_failures": payment_failures,
        },
    }
    sales_profile = sb.table("customer_sales_profiles").upsert(sales_row, on_conflict="profile_id").execute().data[0]

    customer_update = {
        "id": customer["id"],
        "plan_code": plan_code,
        "lifecycle_stage": lifecycle_stage,
        "last_active_at": last_seen_at.isoformat() if last_seen_at else customer.get("last_active_at"),
        "first_paid_at": first_value_at.isoformat() if first_value_at else customer.get("first_paid_at"),
        "total_orders": total_orders,
        "total_revenue_cents": total_revenue_cents,
        "monthly_recurring_revenue_cents": monthly_recurring_cents,
        "lifetime_value_cents": total_revenue_cents,
        "upgrade_propensity_score": upgrade_score,
        "churn_risk_score": churn_risk,
    }
    sb.table("billing_customers").upsert(customer_update, on_conflict="id").execute()
    return sales_profile


def record_profile_activity(profile_id: str, event_type: str, event_row: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    profile = _get_profile_by_id(profile_id)
    if not profile:
        return None

    sb = get_supabase()
    usage_date = _date_from_event(event_row)
    existing_res = (
        sb.table("profile_usage_daily")
        .select("*")
        .eq("profile_id", profile_id)
        .eq("usage_date", usage_date.isoformat())
        .limit(1)
        .execute()
    )
    existing = existing_res.data[0] if existing_res.data else {}
    row = existing.copy()
    row.update({
        "profile_id": profile_id,
        "usage_date": usage_date.isoformat(),
        "plan_code": _clean_text(profile.get("plan")) or row.get("plan_code") or "free",
        "event_count": int(row.get("event_count") or 0) + 1,
        "last_event_at": (_iso_to_datetime(event_row.get("created_at")) or _utcnow()).isoformat(),
        "top_topics": _topic_with_weight(row.get("top_topics") or [], event_row.get("topic"), float(event_row.get("event_value") or 1)),
        "metadata": _merge_dicts(row.get("metadata"), {
            "last_event_type": event_type,
            "last_title": _truncate_text(event_row.get("title")),
        }),
    })

    for counter_name in DAILY_COUNTERS.values():
        row[counter_name] = int(row.get(counter_name) or 0)
    counter = DAILY_COUNTERS.get(event_type)
    if counter:
        row[counter] += 1

    usage_row = sb.table("profile_usage_daily").upsert(row, on_conflict="profile_id,usage_date").execute().data[0]

    customer = ensure_billing_customer_for_profile(profile)
    sb.table("billing_customers").upsert({
        "id": customer["id"],
        "last_active_at": row["last_event_at"],
        "plan_code": row["plan_code"],
    }, on_conflict="id").execute()

    existing_sales = (
        sb.table("customer_sales_profiles")
        .select("*")
        .eq("profile_id", profile_id)
        .limit(1)
        .execute()
        .data
    )
    sales_row = existing_sales[0] if existing_sales else {}
    updates = {
        "profile_id": profile_id,
        "billing_customer_id": customer["id"],
        "current_plan_code": row["plan_code"],
        "recent_activity": _recent_activity(sales_row.get("recent_activity") or [], event_row),
        "top_topics": _topic_with_weight(sales_row.get("top_topics") or [], event_row.get("topic"), float(event_row.get("event_value") or 1)),
        "last_seen_at": row["last_event_at"],
    }
    counter_name = SALES_COUNTERS.get(event_type)
    if counter_name:
        updates[counter_name] = int(sales_row.get(counter_name) or 0) + 1
    sb.table("customer_sales_profiles").upsert({**sales_row, **updates}, on_conflict="profile_id").execute()

    return refresh_customer_sales_profile(profile_id) if customer else usage_row


def ingest_clerk_webhook(payload: Dict[str, Any]) -> Dict[str, Any]:
    event_type = _clean_text(payload.get("type")) or "unknown"
    data = payload.get("data") or {}

    if event_type == "user.deleted":
        clerk_user_id = _clean_text(data.get("id"))
        profile = get_profile_by_clerk_user_id(clerk_user_id) if clerk_user_id else None
        if profile:
            customer = _get_customer_for_profile(profile["id"])
            if customer:
                get_supabase().table("billing_customers").upsert({
                    "id": customer["id"],
                    "is_active": False,
                    "lifecycle_stage": "archived",
                }, on_conflict="id").execute()
        return {
            "success": True,
            "event_type": event_type,
            "action": "archived",
        }

    email_addresses = data.get("email_addresses") or []
    primary_email = None
    primary_email_id = data.get("primary_email_address_id")
    for item in email_addresses:
        if item.get("id") == primary_email_id:
            primary_email = item.get("email_address")
            break
    if not primary_email and email_addresses:
        primary_email = email_addresses[0].get("email_address")

    profile_payload = {
        "clerk_user_id": data.get("id"),
        "email": primary_email,
        "full_name": " ".join(part for part in [data.get("first_name"), data.get("last_name")] if part).strip() or data.get("username"),
        "first_name": data.get("first_name"),
        "last_name": data.get("last_name"),
        "avatar_url": data.get("image_url"),
        "plan": (
            _clean_text((data.get("public_metadata") or {}).get("plan"))
            or _clean_text((data.get("unsafe_metadata") or {}).get("plan"))
            or "free"
        ),
        "auth_provider": "clerk",
    }
    profile = create_or_update_profile({key: value for key, value in profile_payload.items() if value is not None})
    sync_result = sync_profile_to_business_records(
        profile,
        acquisition_context={
            "acquisition_channel": _clean_text((data.get("public_metadata") or {}).get("acquisition_channel")),
            "marketing_campaign": _clean_text((data.get("public_metadata") or {}).get("marketing_campaign")),
            "conversion_source": "clerk_webhook",
            "metadata": {
                "clerk_event_type": event_type,
            },
        },
    )
    return {
        "success": True,
        "event_type": event_type,
        "profile": profile,
        **sync_result,
    }


def _resolve_profile_for_stripe_object(obj: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    metadata = obj.get("metadata") or {}
    clerk_user_id = _clean_text(metadata.get("clerk_user_id"))
    if clerk_user_id:
        profile = get_profile_by_clerk_user_id(clerk_user_id)
        if profile:
            return profile
    profile = _get_profile_by_email(obj.get("customer_email") or obj.get("email"))
    if profile:
        return profile
    customer_id = _clean_text(obj.get("customer"))
    customer = _get_customer_for_stripe_id(customer_id)
    if customer and customer.get("profile_id"):
        return _get_profile_by_id(customer["profile_id"])
    return None


def _log_stripe_event(payload: Dict[str, Any], status: str = "received", error_message: Optional[str] = None) -> Dict[str, Any]:
    row = {
        "stripe_event_id": _clean_text(payload.get("id")) or f"local-{_utcnow().timestamp()}",
        "event_type": _clean_text(payload.get("type")) or "unknown",
        "livemode": bool(payload.get("livemode") or False),
        "api_version": _clean_text(payload.get("api_version")),
        "status": status,
        "processed_at": _utcnow().isoformat() if status in {"processed", "failed"} else None,
        "error_message": error_message,
        "payload": payload,
    }
    res = get_supabase().table("stripe_event_log").upsert(row, on_conflict="stripe_event_id").execute()
    return res.data[0]


def ingest_stripe_event(payload: Dict[str, Any]) -> Dict[str, Any]:
    sb = get_supabase()
    event_log = _log_stripe_event(payload)
    event_type = _clean_text(payload.get("type")) or "unknown"
    obj = ((payload.get("data") or {}).get("object")) or {}
    profile = _resolve_profile_for_stripe_object(obj)
    profile_id = profile.get("id") if profile else None

    if profile:
        customer = ensure_billing_customer_for_profile(profile)
        stripe_customer_id = _clean_text(obj.get("customer")) or _clean_text(obj.get("id"))
        customer_row = {
            "id": customer["id"],
            "stripe_customer_id": stripe_customer_id if event_type.startswith("customer.") or obj.get("object") == "customer" else customer.get("stripe_customer_id"),
            "email": obj.get("customer_email") or obj.get("email") or customer.get("email"),
            "full_name": obj.get("customer_details", {}).get("name") or obj.get("name") or customer.get("full_name"),
            "plan_code": _clean_text((obj.get("metadata") or {}).get("plan_code")) or customer.get("plan_code"),
            "metadata": _merge_dicts(customer.get("metadata"), {
                "last_stripe_event_type": event_type,
            }),
        }
        sb.table("billing_customers").upsert(customer_row, on_conflict="id").execute()

    if event_type.startswith("customer.subscription."):
        customer = _get_customer_for_stripe_id(_clean_text(obj.get("customer"))) if obj.get("customer") else (_get_customer_for_profile(profile_id) if profile_id else None)
        plan = None
        items = (((obj.get("items") or {}).get("data")) or [])
        if items:
            price = (items[0] or {}).get("price") or {}
            plan = price.get("lookup_key") or price.get("nickname")
        plan_code = _clean_text((obj.get("metadata") or {}).get("plan_code")) or _clean_text(plan) or (customer or {}).get("plan_code") or "free"
        subscription_row = {
            "profile_id": profile_id,
            "billing_customer_id": (customer or {}).get("id"),
            "stripe_subscription_id": obj.get("id"),
            "stripe_customer_id": obj.get("customer"),
            "plan_code": plan_code,
            "status": obj.get("status") or "incomplete",
            "billing_interval": (((items[0] or {}).get("price") or {}).get("recurring") or {}).get("interval") or "month",
            "currency": (((items[0] or {}).get("price") or {}).get("currency")) or "usd",
            "unit_amount_cents": int((((items[0] or {}).get("price") or {}).get("unit_amount")) or 0),
            "seats": int((obj.get("quantity") or 1)),
            "current_period_start": _iso_to_datetime(obj.get("current_period_start")).isoformat() if _iso_to_datetime(obj.get("current_period_start")) else None,
            "current_period_end": _iso_to_datetime(obj.get("current_period_end")).isoformat() if _iso_to_datetime(obj.get("current_period_end")) else None,
            "cancel_at_period_end": bool(obj.get("cancel_at_period_end") or False),
            "canceled_at": _iso_to_datetime(obj.get("canceled_at")).isoformat() if _iso_to_datetime(obj.get("canceled_at")) else None,
            "trial_end": _iso_to_datetime(obj.get("trial_end")).isoformat() if _iso_to_datetime(obj.get("trial_end")) else None,
            "metadata": obj.get("metadata") or {},
        }
        sb.table("billing_subscriptions").upsert(subscription_row, on_conflict="stripe_subscription_id").execute()

    if event_type in {"checkout.session.completed", "invoice.paid", "invoice.payment_failed"}:
        customer = _get_customer_for_stripe_id(_clean_text(obj.get("customer"))) if obj.get("customer") else (_get_customer_for_profile(profile_id) if profile_id else None)
        subscriptions = []
        if profile_id:
            subscriptions = (
                sb.table("billing_subscriptions")
                .select("*")
                .eq("profile_id", profile_id)
                .order("updated_at", desc=True)
                .limit(1)
                .execute()
                .data
                or []
            )
        subscription = subscriptions[0] if subscriptions else None
        transaction_row = {
            "profile_id": profile_id,
            "billing_customer_id": (customer or {}).get("id"),
            "subscription_id": (subscription or {}).get("id"),
            "stripe_invoice_id": obj.get("invoice") or obj.get("id"),
            "stripe_payment_intent_id": obj.get("payment_intent"),
            "stripe_checkout_session_id": obj.get("id") if event_type == "checkout.session.completed" else None,
            "transaction_type": "checkout_session" if event_type == "checkout.session.completed" else "invoice",
            "status": "paid" if event_type in {"checkout.session.completed", "invoice.paid"} else "payment_failed",
            "currency": obj.get("currency") or "usd",
            "amount_subtotal_cents": int(obj.get("amount_subtotal") or obj.get("subtotal") or obj.get("amount_total") or 0),
            "amount_discount_cents": int((((obj.get("total_details") or {}).get("amount_discount")) or 0)),
            "amount_tax_cents": int((((obj.get("total_details") or {}).get("amount_tax")) or 0)),
            "amount_total_cents": int(obj.get("amount_total") or obj.get("total") or 0),
            "collected_at": (_iso_to_datetime(obj.get("created")) or _utcnow()).isoformat(),
            "metadata": {
                "event_type": event_type,
                "mode": obj.get("mode"),
                "payment_status": obj.get("payment_status"),
            },
        }
        sb.table("billing_transactions").upsert(transaction_row, on_conflict="stripe_invoice_id").execute()

    if profile_id:
        refresh_customer_sales_profile(profile_id)

    _log_stripe_event(payload, status="processed")
    return {
        "success": True,
        "event_id": event_log["stripe_event_id"],
        "event_type": event_type,
        "profile_id": profile_id,
    }


def get_customer_sales_profile(clerk_user_id: str) -> Dict[str, Any]:
    profile = get_profile_by_clerk_user_id(clerk_user_id)
    if not profile:
        raise ValueError("Profile not found")

    sales_profile = refresh_customer_sales_profile(profile["id"])
    customer = _get_customer_for_profile(profile["id"])
    subscriptions = (
        get_supabase()
        .table("billing_subscriptions")
        .select("*")
        .eq("profile_id", profile["id"])
        .order("updated_at", desc=True)
        .limit(10)
        .execute()
        .data
        or []
    )
    transactions = (
        get_supabase()
        .table("billing_transactions")
        .select("*")
        .eq("profile_id", profile["id"])
        .order("collected_at", desc=True)
        .limit(10)
        .execute()
        .data
        or []
    )
    return {
        "profile": profile,
        "customer": customer,
        "sales_profile": sales_profile,
        "subscriptions": subscriptions,
        "transactions": transactions,
    }


def list_customer_sales_profiles(limit: int = 25) -> List[Dict[str, Any]]:
    res = (
        get_supabase()
        .table("customer_sales_profiles")
        .select("*, profiles!inner(clerk_user_id,email,full_name)")
        .order("health_score", desc=True)
        .limit(limit)
        .execute()
    )
    return res.data or []


def list_team_members() -> List[Dict[str, Any]]:
    res = (
        get_supabase()
        .table("team_members")
        .select("*")
        .order("department")
        .order("full_name")
        .execute()
    )
    return res.data or []


def get_admin_dashboard_overview(days: int = 30) -> Dict[str, Any]:
    sb = get_supabase()
    days = max(1, min(days, 365))
    since = (_utcnow() - timedelta(days=days)).isoformat()

    profiles = sb.table("profiles").select("*").execute().data or []
    customers = sb.table("billing_customers").select("*").execute().data or []
    sales_profiles = sb.table("customer_sales_profiles").select("*").execute().data or []
    subscriptions = sb.table("billing_subscriptions").select("*").execute().data or []
    transactions = (
        sb.table("billing_transactions")
        .select("*")
        .gte("created_at", since)
        .order("created_at", desc=True)
        .execute()
        .data
        or []
    )
    usage_rows = (
        sb.table("profile_usage_daily")
        .select("*")
        .gte("usage_date", (_utcnow() - timedelta(days=days)).date().isoformat())
        .execute()
        .data
        or []
    )

    paid_transactions = [row for row in transactions if row.get("status") in {"paid", "succeeded", "complete"}]
    active_subscriptions = [row for row in subscriptions if row.get("status") in {"active", "trialing", "past_due"}]
    paid_customers = [row for row in customers if (row.get("plan_code") or "free") != "free"]
    upgrade_candidates = sorted(
        sales_profiles,
        key=lambda row: float(row.get("upgrade_propensity_score") or 0),
        reverse=True,
    )[:5]
    top_revenue_accounts = sorted(
        sales_profiles,
        key=lambda row: int(row.get("total_revenue_cents") or 0),
        reverse=True,
    )[:5]

    mrr_cents = sum(int(row.get("unit_amount_cents") or 0) for row in active_subscriptions)
    revenue_cents = sum(int(row.get("amount_total_cents") or 0) for row in paid_transactions)
    searches = sum(int(row.get("search_count") or 0) for row in usage_rows)
    views = sum(int(row.get("view_count") or 0) for row in usage_rows)
    compares = sum(int(row.get("compare_count") or 0) for row in usage_rows)
    uploads = sum(int(row.get("upload_count") or 0) for row in usage_rows)

    plan_mix: Dict[str, int] = {}
    for row in customers:
        plan = _clean_text(row.get("plan_code")) or "free"
        plan_mix[plan] = plan_mix.get(plan, 0) + 1

    return {
        "window_days": days,
        "totals": {
            "profiles": len(profiles),
            "customers": len(customers),
            "paid_customers": len(paid_customers),
            "active_subscriptions": len(active_subscriptions),
            "transactions": len(paid_transactions),
            "mrr_cents": mrr_cents,
            "revenue_cents": revenue_cents,
            "searches": searches,
            "views": views,
            "compares": compares,
            "uploads": uploads,
        },
        "plan_mix": [{"plan_code": plan, "count": count} for plan, count in sorted(plan_mix.items())],
        "upgrade_candidates": upgrade_candidates,
        "top_revenue_accounts": top_revenue_accounts,
        "recent_transactions": paid_transactions[:10],
        "team_members": list_team_members(),
    }
