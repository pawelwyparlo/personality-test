"""Coach API tests (real Postgres; fake Clerk verifier + fake streaming LLM).

The Clerk JWT verifier is overridden so tests never touch a real Clerk instance:
a bearer token of the form ``fake:<account_id>`` verifies to that account. The
LLM is swapped for a fake streaming client. Covers the 503s (auth and llm,
separately), claim semantics, message-persistence order, SSE assembly, and the
GET 404/200 shapes.
"""

from __future__ import annotations

from typing import AsyncIterator

import pytest

from app.auth import clerk as clerk_auth
from app.core.config import Settings, get_settings
from app.llm import factory as llm_factory
from app.main import app

pytestmark = pytest.mark.asyncio


# --- Test doubles ----------------------------------------------------------- #


def _fake_verifier(token: str, secret_key: str) -> dict:
    """Bearer ``fake:<sub>`` verifies to that subject; anything else is invalid."""
    if not token.startswith("fake:"):
        raise ValueError("bad token")
    return {"sub": token.split(":", 1)[1]}


class FakeStreamLLM:
    """Streams a fixed reply as several chunks; records the calls it received."""

    def __init__(self, chunks: list[str]):
        self._chunks = chunks
        self.calls: list[tuple[str, list[dict]]] = []

    def stream_text(
        self, system: str, messages: list[dict[str, str]]
    ) -> AsyncIterator[str]:
        self.calls.append((system, messages))

        async def gen():
            for c in self._chunks:
                yield c

        return gen()


@pytest.fixture(autouse=True)
def _reset_overrides():
    """Ensure a clean slate of dependency/verifier overrides per test."""
    yield
    clerk_auth.set_verifier(None)
    app.dependency_overrides.pop(get_settings, None)
    get_settings.cache_clear()


def _configure_clerk(secret: str = "sk_test_x"):
    """Point the auth dependency at a configured Clerk secret + fake verifier."""
    app.dependency_overrides[get_settings] = lambda: Settings(clerk_secret_key=secret)
    clerk_auth.set_verifier(_fake_verifier)


def _auth(account_id: str) -> dict:
    return {"Authorization": f"Bearer fake:{account_id}"}


def _use_llm(monkeypatch, client_obj):
    """Force the coach endpoint's LLM factory to return ``client_obj``."""
    monkeypatch.setattr(llm_factory, "_build", lambda settings: client_obj)


# --- Helpers over the test API ---------------------------------------------- #


async def _completed_profile(client) -> str:
    """Create a Profile with one completed Full run; return the profile id."""
    prof = await client.post("/api/v1/profiles")
    profile_id = prof.json()["id"]
    run = await client.post(
        "/api/v1/test-runs",
        json={"profile_id": profile_id, "form": "full", "age": 30, "sex": "male"},
    )
    run_id = run.json()["id"]
    for i in range(1, 121):
        r = await client.post(
            f"/api/v1/test-runs/{run_id}/answers",
            json={"item_id": i, "value": ((i * 7) % 5) + 1},
        )
        assert r.status_code == 204, r.text
    done = await client.post(f"/api/v1/test-runs/{run_id}/complete")
    assert done.status_code == 200, done.text
    return profile_id


# --- 503s when unconfigured ------------------------------------------------- #


async def test_coach_requires_auth_config(client):
    # No Clerk secret configured -> 503 auth_not_configured, regardless of body.
    app.dependency_overrides[get_settings] = lambda: Settings(clerk_secret_key="")
    clerk_auth.set_verifier(_fake_verifier)
    resp = await client.post(
        "/api/v1/coach",
        json={"profile_id": "00000000-0000-0000-0000-000000000000"},
        headers=_auth("acct_1"),
    )
    assert resp.status_code == 503
    assert resp.json()["detail"] == "auth_not_configured"


async def test_message_llm_not_configured_503_before_persist(client, monkeypatch):
    _configure_clerk()
    from app.llm.null import NullClient

    _use_llm(monkeypatch, NullClient())

    profile_id = await _completed_profile(client)
    created = await client.post(
        "/api/v1/coach", json={"profile_id": profile_id}, headers=_auth("acct_llm")
    )
    assert created.status_code == 201

    resp = await client.post(
        "/api/v1/coach/messages",
        json={"content": "hello"},
        headers=_auth("acct_llm"),
    )
    assert resp.status_code == 503
    assert resp.json()["detail"] == "llm_not_configured"

    # The user message must NOT have been persisted (no orphan turn).
    got = await client.get("/api/v1/coach", headers=_auth("acct_llm"))
    assert got.status_code == 200
    assert got.json()["messages"] == []


# --- Claim semantics -------------------------------------------------------- #


async def test_create_coach_happy_path(client):
    _configure_clerk()
    profile_id = await _completed_profile(client)
    resp = await client.post(
        "/api/v1/coach", json={"profile_id": profile_id}, headers=_auth("acct_a")
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "Sol"
    assert body["id"]


async def test_reclaim_own_profile_is_conflict_not_error(client):
    _configure_clerk()
    profile_id = await _completed_profile(client)
    first = await client.post(
        "/api/v1/coach", json={"profile_id": profile_id}, headers=_auth("acct_b")
    )
    assert first.status_code == 201
    # Same account, same profile -> the coach already exists (409), not a crash.
    again = await client.post(
        "/api/v1/coach", json={"profile_id": profile_id}, headers=_auth("acct_b")
    )
    assert again.status_code == 409


async def test_claiming_another_accounts_profile_conflicts(client):
    _configure_clerk()
    profile_id = await _completed_profile(client)
    first = await client.post(
        "/api/v1/coach", json={"profile_id": profile_id}, headers=_auth("owner")
    )
    assert first.status_code == 201
    # A different account tries to claim the same profile.
    intruder = await client.post(
        "/api/v1/coach", json={"profile_id": profile_id}, headers=_auth("intruder")
    )
    assert intruder.status_code == 409


async def test_account_cannot_claim_a_second_profile(client):
    _configure_clerk()
    p1 = await _completed_profile(client)
    p2 = await _completed_profile(client)
    ok = await client.post(
        "/api/v1/coach", json={"profile_id": p1}, headers=_auth("multi")
    )
    assert ok.status_code == 201
    second = await client.post(
        "/api/v1/coach", json={"profile_id": p2}, headers=_auth("multi")
    )
    assert second.status_code == 409


async def test_create_coach_requires_completed_run(client):
    _configure_clerk()
    prof = await client.post("/api/v1/profiles")
    profile_id = prof.json()["id"]
    # No completed run on this profile.
    resp = await client.post(
        "/api/v1/coach", json={"profile_id": profile_id}, headers=_auth("acct_no_run")
    )
    assert resp.status_code == 409
    assert "completed test run" in resp.json()["detail"]


async def test_create_coach_missing_profile_404(client):
    _configure_clerk()
    resp = await client.post(
        "/api/v1/coach",
        json={"profile_id": "00000000-0000-0000-0000-000000000001"},
        headers=_auth("acct_x"),
    )
    assert resp.status_code == 404


# --- GET shapes ------------------------------------------------------------- #


async def test_get_coach_404_when_none(client):
    _configure_clerk()
    resp = await client.get("/api/v1/coach", headers=_auth("nobody"))
    assert resp.status_code == 404


async def test_get_coach_returns_context_and_messages(client):
    _configure_clerk()
    profile_id = await _completed_profile(client)
    await client.post(
        "/api/v1/coach", json={"profile_id": profile_id}, headers=_auth("acct_g")
    )
    resp = await client.get("/api/v1/coach", headers=_auth("acct_g"))
    assert resp.status_code == 200
    body = resp.json()
    assert body["name"] == "Sol"
    assert body["messages"] == []
    ctx = body["trait_context"]
    assert set(ctx["percentiles"]) == {"O", "C", "E", "A", "N"}
    assert ctx["run_id"]
    for v in ctx["percentiles"].values():
        assert 1 <= v <= 99


# --- Messaging + SSE assembly ---------------------------------------------- #


async def test_message_streams_and_persists_in_order(client, monkeypatch):
    _configure_clerk()
    _use_llm(monkeypatch, FakeStreamLLM(["Hel", "lo ", "there"]))

    profile_id = await _completed_profile(client)
    await client.post(
        "/api/v1/coach", json={"profile_id": profile_id}, headers=_auth("acct_m")
    )

    resp = await client.post(
        "/api/v1/coach/messages",
        json={"content": "Hi Sol"},
        headers=_auth("acct_m"),
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/event-stream")
    # Reassemble the streamed tokens from the SSE body.
    body = resp.text
    assert "Hel" in body and "lo " in body and "there" in body

    # After the stream, the thread is [user, coach] in chronological order.
    got = (await client.get("/api/v1/coach", headers=_auth("acct_m"))).json()
    roles = [m["role"] for m in got["messages"]]
    assert roles == ["user", "coach"]
    assert got["messages"][0]["content"] == "Hi Sol"
    assert got["messages"][1]["content"] == "Hello there"


async def test_message_prompt_is_grounded_in_scores(client, monkeypatch):
    _configure_clerk()
    fake = FakeStreamLLM(["ok"])
    _use_llm(monkeypatch, fake)

    profile_id = await _completed_profile(client)
    await client.post(
        "/api/v1/coach", json={"profile_id": profile_id}, headers=_auth("acct_p")
    )
    await client.post(
        "/api/v1/coach/messages",
        json={"content": "What are my strengths?"},
        headers=_auth("acct_p"),
    )
    assert fake.calls, "the LLM should have been called"
    system, window = fake.calls[0]
    assert "Sol" in system
    assert "percentile" in system
    assert "never invent" in system.lower() or "never invent scores" in system.lower()
    # The rolling window ends with the new user turn.
    assert window[-1] == {"role": "user", "content": "What are my strengths?"}


async def test_message_404_without_coach(client, monkeypatch):
    _configure_clerk()
    _use_llm(monkeypatch, FakeStreamLLM(["x"]))
    resp = await client.post(
        "/api/v1/coach/messages",
        json={"content": "hello"},
        headers=_auth("acct_nocoach"),
    )
    assert resp.status_code == 404


async def test_empty_message_rejected(client, monkeypatch):
    _configure_clerk()
    _use_llm(monkeypatch, FakeStreamLLM(["x"]))
    profile_id = await _completed_profile(client)
    await client.post(
        "/api/v1/coach", json={"profile_id": profile_id}, headers=_auth("acct_e")
    )
    resp = await client.post(
        "/api/v1/coach/messages",
        json={"content": "   "},
        headers=_auth("acct_e"),
    )
    assert resp.status_code == 422
