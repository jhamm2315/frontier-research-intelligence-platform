from __future__ import annotations

from typing import Any

from fastapi import HTTPException, Request

from app.config import get_settings
from app.services.clerk_auth_service import require_verified_clerk_user
from app.services.local_state_service import get_local_profile
from app.services.persistence_service import get_profile_by_clerk_user_id


def get_admin_identity(request: Request) -> dict[str, Any]:
    settings = get_settings()
    identity = require_verified_clerk_user(request)
    clerk_user_id = identity["clerk_user_id"]

    if clerk_user_id in settings.admin_clerk_user_ids:
        return {
            "clerk_user_id": clerk_user_id,
            "is_admin": True,
            "source": "env_allowlist",
            "session_claims": identity.get("session_claims", {}),
        }

    profile = None
    try:
        profile = get_profile_by_clerk_user_id(clerk_user_id)
    except Exception:
        profile = None

    if not profile:
        profile = get_local_profile(clerk_user_id)

    if profile and profile.get("is_admin") is True:
        return {
            "clerk_user_id": clerk_user_id,
            "is_admin": True,
            "source": "profile_flag",
            "profile": profile,
            "session_claims": identity.get("session_claims", {}),
        }

    raise HTTPException(status_code=403, detail="Admin privileges required.")


def require_admin(request: Request) -> dict[str, Any]:
    return get_admin_identity(request)
