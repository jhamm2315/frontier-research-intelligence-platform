from __future__ import annotations

import hashlib
import hmac
import json
import time
from typing import Any

import requests

from app.config import get_settings


class StripeConfigError(ValueError):
    pass


def create_checkout_session(
    *,
    plan_code: str,
    clerk_user_id: str,
    email: str | None = None,
    success_url: str | None = None,
    cancel_url: str | None = None,
) -> dict[str, Any]:
    settings = get_settings()
    if not settings.stripe_secret_key:
        raise StripeConfigError("STRIPE_SECRET_KEY is not configured.")

    price_id = (settings.stripe_price_ids or {}).get(plan_code)
    if not price_id:
        raise StripeConfigError(f"No Stripe price configured for plan: {plan_code}")

    payload = {
        "mode": "subscription",
        "success_url": success_url or f"{settings.app_base_url}/workspace?checkout=success&plan={plan_code}",
        "cancel_url": cancel_url or f"{settings.app_base_url}/pricing?checkout=cancelled&plan={plan_code}",
        "line_items[0][price]": price_id,
        "line_items[0][quantity]": "1",
        "client_reference_id": clerk_user_id,
        "metadata[clerk_user_id]": clerk_user_id,
        "metadata[plan_code]": plan_code,
        "allow_promotion_codes": "true",
    }
    if email:
        payload["customer_email"] = email

    response = requests.post(
        "https://api.stripe.com/v1/checkout/sessions",
        auth=(settings.stripe_secret_key, ""),
        data=payload,
        timeout=20,
    )
    if not response.ok:
        raise StripeConfigError(f"Stripe checkout session failed ({response.status_code}): {response.text[:300]}")
    return response.json()


def verify_stripe_webhook_signature(payload: bytes, signature_header: str | None) -> bool:
    settings = get_settings()
    secret = settings.stripe_webhook_secret
    if not secret:
        return False
    if not signature_header:
        return False

    parts = {}
    for chunk in signature_header.split(","):
        if "=" not in chunk:
            continue
        key, value = chunk.split("=", 1)
        parts[key.strip()] = value.strip()

    timestamp = parts.get("t")
    signature = parts.get("v1")
    if not timestamp or not signature:
        return False

    signed_payload = f"{timestamp}.{payload.decode('utf-8')}".encode("utf-8")
    expected = hmac.new(secret.encode("utf-8"), signed_payload, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        return False

    try:
        event_age = abs(time.time() - int(timestamp))
    except ValueError:
        return False
    return event_age <= 300


def parse_stripe_webhook_payload(payload: bytes) -> dict[str, Any]:
    return json.loads(payload.decode("utf-8"))
