"""Clerk session-JWT verification (ADR-0002).

The Coach endpoints are gated on a signed-in Account. A request carries the
Clerk session JWT in ``Authorization: Bearer <token>``; we verify it with the
official ``clerk-backend-api`` SDK's **networkless** ``verify_token`` (JWKS
fetched and cached by the SDK, keyed off ``CLERK_SECRET_KEY``) and return the
Clerk user id (the token's ``sub``) as the authenticated Account identity.

Keyless degradation: with no ``CLERK_SECRET_KEY`` the dependency raises
503 ``auth_not_configured`` — never a 500, never a crash at import/startup.

Testability: the JWT-verification callable is injected via a module-level
``_verifier`` and overridable with :func:`set_verifier` (tests swap in a fake so
no real Clerk instance is needed).
"""

from __future__ import annotations

from typing import Callable

from fastapi import Depends, Header, HTTPException

from app.core.config import Settings, get_settings

# A verifier takes (token, secret_key) and returns the decoded payload dict
# (which carries the Clerk user id under "sub"). Raises on an invalid token.
Verifier = Callable[[str, str], dict]


def _default_verifier(token: str, secret_key: str) -> dict:
    """Networkless verification via the Clerk SDK (imported lazily).

    The SDK is only imported when a real verification happens, so a keyless
    deployment that never reaches here doesn't need it installed and nothing
    fails at import time.
    """
    from clerk_backend_api.security.verifytoken import verify_token
    from clerk_backend_api.security.types import VerifyTokenOptions

    return verify_token(token, VerifyTokenOptions(secret_key=secret_key))


# Overridable for tests; production uses the SDK-backed verifier.
_verifier: Verifier = _default_verifier


def set_verifier(verifier: Verifier | None) -> None:
    """Swap the JWT-verification callable (tests inject a fake; ``None`` resets)."""
    global _verifier
    _verifier = verifier or _default_verifier


def _extract_bearer(authorization: str | None) -> str:
    if not authorization:
        raise HTTPException(status_code=401, detail="missing bearer token")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise HTTPException(status_code=401, detail="invalid authorization header")
    return token.strip()


async def require_account(
    authorization: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
) -> str:
    """FastAPI dependency: verify the Clerk session and return the Account id.

    * No ``CLERK_SECRET_KEY`` configured -> 503 ``auth_not_configured``.
    * Missing / malformed bearer -> 401.
    * Token fails verification -> 401.
    * Success -> the Clerk user id (``sub`` claim), i.e. the Account identity.
    """
    secret_key = settings.clerk_secret_key.strip()
    if not secret_key:
        raise HTTPException(status_code=503, detail="auth_not_configured")

    token = _extract_bearer(authorization)
    try:
        payload = _verifier(token, secret_key)
    except HTTPException:
        raise
    except Exception as exc:  # invalid/expired token, JWKS failure, etc.
        raise HTTPException(status_code=401, detail="invalid session token") from exc

    account_id = payload.get("sub") if isinstance(payload, dict) else None
    if not account_id:
        raise HTTPException(status_code=401, detail="session token missing subject")
    return account_id
