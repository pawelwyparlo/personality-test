"""Thin LLM adapter (ADR-0003).

A single small :class:`LLMClient` protocol with a Vertex AI implementation and a
null implementation, plus a factory that reads settings. The app must run with no
key configured — the factory then returns a :class:`NullClient` and never raises
at import or startup. Callers that need generation catch :class:`LLMUnavailable`
and fall back (the report drops to the deterministic text bank).
"""

from __future__ import annotations

from app.llm.base import LLMClient, LLMUnavailable
from app.llm.factory import get_llm_client
from app.llm.null import NullClient

__all__ = ["LLMClient", "LLMUnavailable", "NullClient", "get_llm_client"]
