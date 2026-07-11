"""Unit tests for the Clerk auth dependency and the coach prompt builder.

No DB or real Clerk instance: the verifier is injected and settings are built
in-memory. These assert the keyless 503, the 401 paths, and that the prompt is
grounded in the real scores with the anti-invention rule.
"""

from __future__ import annotations

import pytest
from fastapi import HTTPException

from app.auth.clerk import require_account, set_verifier
from app.coach.prompt import build_system_prompt, trait_context_line
from app.core.config import Settings

# asyncio_mode = "auto" (pyproject) runs the async tests; the sync prompt tests
# below must not carry an asyncio mark, so there is no module-level pytestmark.


def _fake_verifier(token: str, secret_key: str) -> dict:
    if token == "good":
        return {"sub": "user_123"}
    raise ValueError("bad")


async def test_require_account_keyless_503():
    set_verifier(_fake_verifier)
    try:
        with pytest.raises(HTTPException) as exc:
            await require_account(
                authorization="Bearer good", settings=Settings(clerk_secret_key="")
            )
        assert exc.value.status_code == 503
        assert exc.value.detail == "auth_not_configured"
    finally:
        set_verifier(None)


async def test_require_account_missing_bearer_401():
    set_verifier(_fake_verifier)
    try:
        with pytest.raises(HTTPException) as exc:
            await require_account(
                authorization=None, settings=Settings(clerk_secret_key="sk")
            )
        assert exc.value.status_code == 401
    finally:
        set_verifier(None)


async def test_require_account_bad_token_401():
    set_verifier(_fake_verifier)
    try:
        with pytest.raises(HTTPException) as exc:
            await require_account(
                authorization="Bearer nope", settings=Settings(clerk_secret_key="sk")
            )
        assert exc.value.status_code == 401
    finally:
        set_verifier(None)


async def test_require_account_success_returns_sub():
    set_verifier(_fake_verifier)
    try:
        account = await require_account(
            authorization="Bearer good", settings=Settings(clerk_secret_key="sk")
        )
        assert account == "user_123"
    finally:
        set_verifier(None)


def _scores() -> dict:
    doms = [
        ("O", "Openness", 72, "high"),
        ("C", "Conscientiousness", 84, "high"),
        ("E", "Extraversion", 38, "low"),
        ("A", "Agreeableness", 61, "average"),
        ("N", "Neuroticism", 29, "low"),
    ]
    domains = []
    for letter, name, pct, level in doms:
        domains.append(
            {
                "domain": letter,
                "name": name,
                "raw": 96,
                "t_score": 55.0,
                "percentile": pct,
                "level": level,
                "facets": [
                    {
                        "domain": letter,
                        "number": 1,
                        "name": f"{name[:4]}Facet",
                        "raw": 16,
                        "t_score": 55.0,
                        "percentile": pct,
                        "level": level,
                    }
                ],
            }
        )
    return {"domains": domains}


def test_trait_context_line_is_ocean_percentiles():
    ctx = trait_context_line(_scores())
    assert ctx == {"O": 72, "C": 84, "E": 38, "A": 61, "N": 29}


def test_system_prompt_grounded_and_named():
    prompt = build_system_prompt(_scores(), coach_name="Sol")
    assert "Sol" in prompt
    assert "72th percentile" in prompt
    assert "Openness" in prompt
    assert "NEVER invent scores" in prompt
