from __future__ import annotations

import json
from typing import Any

import jwt
from fastapi import HTTPException, Request
from jwt import InvalidTokenError
from jwt.algorithms import RSAAlgorithm

from app.config import Settings, get_settings


def _extract_session_token(request: Request) -> str | None:
    auth_header = request.headers.get("authorization", "")
    if auth_header.lower().startswith("bearer "):
        token = auth_header.split(" ", 1)[1].strip()
        if token:
            return token

    cookie_candidates = (
        request.cookies.get("__session"),
    )
    for token in cookie_candidates:
        if token and str(token).strip():
            return str(token).strip()
    return None


def _resolve_verification_key(token: str, settings: Settings) -> tuple[Any, list[str]]:
    try:
        header = jwt.get_unverified_header(token)
    except InvalidTokenError as exc:
        raise HTTPException(status_code=401, detail=f"Invalid Clerk session token: {exc}") from exc

    if settings.clerk_jwks_json:
        jwks = json.loads(settings.clerk_jwks_json)
        keys = jwks.get("keys", []) if isinstance(jwks, dict) else []
        kid = header.get("kid")
        for key in keys:
            if kid and key.get("kid") != kid:
                continue
            return RSAAlgorithm.from_jwk(json.dumps(key)), ["RS256"]
        raise HTTPException(status_code=401, detail="Unable to match Clerk signing key.")

    if settings.clerk_jwt_public_key:
        return settings.clerk_jwt_public_key.replace("\\n", "\n"), ["RS256"]

    if settings.clerk_secret_key:
        return settings.clerk_secret_key, ["HS256"]

    raise HTTPException(
        status_code=500,
        detail="Clerk JWT verification is not configured on the server.",
    )


def verify_clerk_session(request: Request) -> dict[str, Any]:
    settings = get_settings()
    token = _extract_session_token(request)
    if not token:
        raise HTTPException(status_code=401, detail="A verified Clerk session is required.")

    verification_key, algorithms = _resolve_verification_key(token, settings)
    decode_kwargs: dict[str, Any] = {
        "algorithms": algorithms,
        "leeway": settings.clerk_jwt_leeway_seconds,
        "options": {
            "require": ["sub", "exp", "iat"],
        },
    }
    if settings.clerk_jwt_issuer:
        decode_kwargs["issuer"] = settings.clerk_jwt_issuer
    if settings.clerk_jwt_audiences:
        decode_kwargs["audience"] = list(settings.clerk_jwt_audiences)

    try:
        claims = jwt.decode(token, verification_key, **decode_kwargs)
    except InvalidTokenError as exc:
        raise HTTPException(status_code=401, detail=f"Invalid Clerk session token: {exc}") from exc

    subject = str(claims.get("sub") or "").strip()
    if not subject:
        raise HTTPException(status_code=401, detail="Verified Clerk token is missing a user subject.")

    if settings.clerk_authorized_parties:
        azp = str(claims.get("azp") or "").strip()
        if azp not in settings.clerk_authorized_parties:
            raise HTTPException(status_code=403, detail="Clerk session is not authorized for this application.")

    return {
        "clerk_user_id": subject,
        "session_claims": claims,
        "session_token": token,
    }


def require_verified_clerk_user(request: Request) -> dict[str, Any]:
    return verify_clerk_session(request)
