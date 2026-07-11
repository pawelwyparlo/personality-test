"""Narrative service tests: LLM path, fallback path, shape guarantees.

A fake in-memory :class:`LLMClient` stands in for Vertex — the real API is never
called. The fallback path is exercised with the :class:`NullClient` (keyless).
"""

from __future__ import annotations

from typing import Any

import pytest

from app.llm.base import LLMUnavailable
from app.llm.null import NullClient
from app.report.narrative import generate_narrative, narrative_fallback

pytestmark = pytest.mark.asyncio


def _scores() -> dict:
    """A minimal but well-formed persisted-scores dict (5 domains, 1 facet each)."""
    doms = [
        ("O", "Openness", 72, "high"),
        ("C", "Conscientiousness", 84, "high"),
        ("E", "Extraversion", 38, "low"),
        ("A", "Agreeableness", 61, "average"),
        ("N", "Neuroticism", 29, "low"),
    ]
    domains = []
    facets = []
    for letter, name, pct, level in doms:
        facet = {
            "domain": letter,
            "number": 1,
            "name": f"{name[:4]}Facet",
            "raw": 16,
            "t_score": 55.0,
            "percentile": pct,
            "level": level,
        }
        facets.append(facet)
        domains.append(
            {
                "domain": letter,
                "name": name,
                "raw": 96,
                "t_score": 55.0,
                "percentile": pct,
                "level": level,
                "facets": [facet],
            }
        )
    return {"run_id": "r", "age": 30, "sex": "male", "domains": domains, "facets": facets}


class FakeLLM:
    """Records the last prompt and returns a canned structured object."""

    def __init__(self, payload: dict[str, Any] | None = None, fail: bool = False):
        self._payload = payload
        self._fail = fail
        self.last_prompt: str | None = None
        self.calls = 0

    async def generate_structured(self, prompt: str, schema: dict) -> dict:
        self.calls += 1
        self.last_prompt = prompt
        if self._fail:
            raise LLMUnavailable("boom")
        return self._payload  # type: ignore[return-value]


async def test_llm_path_returns_source_llm():
    fake = FakeLLM(
        {
            "pull_quote": "A curious, steady planner who recharges alone.",
            "paragraphs": ["Para one.", "Para two."],
            "strengths": ["S1", "S2", "S3"],
            "watch_outs": ["W1", "W2", "W3"],
        }
    )
    out = await generate_narrative(
        _scores(), age=30, sex="male", form="full", llm=fake
    )
    assert out["source"] == "llm"
    assert out["pull_quote"].startswith("A curious")
    assert len(out["paragraphs"]) == 2
    assert len(out["strengths"]) == 3
    assert len(out["watch_outs"]) == 3
    assert fake.calls == 1


async def test_llm_prompt_is_grounded_in_scores():
    fake = FakeLLM(
        {
            "pull_quote": "x",
            "paragraphs": ["a", "b"],
            "strengths": ["1", "2", "3"],
            "watch_outs": ["1", "2", "3"],
        }
    )
    await generate_narrative(_scores(), age=42, sex="female", form="full", llm=fake)
    prompt = fake.last_prompt or ""
    # Real percentiles must appear; the model is told not to invent numbers.
    assert "72th percentile" in prompt
    assert "Openness" in prompt
    assert "age 42" in prompt
    assert "second person" in prompt


async def test_incomplete_llm_output_falls_back():
    # Missing strengths -> treated as unavailable -> text-bank fallback.
    fake = FakeLLM(
        {
            "pull_quote": "x",
            "paragraphs": ["a", "b"],
            "strengths": ["only one"],
            "watch_outs": ["1", "2", "3"],
        }
    )
    out = await generate_narrative(
        _scores(), age=30, sex="male", form="full", llm=fake
    )
    assert out["source"] == "textbank"


async def test_null_client_falls_back():
    out = await generate_narrative(
        _scores(), age=30, sex="male", form="full", llm=NullClient()
    )
    assert out["source"] == "textbank"
    assert out["pull_quote"]
    assert len(out["paragraphs"]) >= 2
    assert len(out["strengths"]) == 3
    assert len(out["watch_outs"]) == 3


@pytest.mark.filterwarnings("ignore::pytest.PytestWarning")
def test_fallback_is_deterministic():
    a = narrative_fallback(_scores())
    b = narrative_fallback(_scores())
    assert a == b
    assert a["source"] == "textbank"
