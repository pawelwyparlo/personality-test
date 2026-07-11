"""The keyless fallback client.

Returned by the factory when no LLM backend is configured. Every generation
attempt raises :class:`LLMUnavailable`, which callers catch to fall back to the
deterministic text bank. Constructing it is always safe.
"""

from __future__ import annotations

from typing import Any

from app.llm.base import LLMUnavailable


class NullClient:
    """An :class:`~app.llm.base.LLMClient` that never generates."""

    async def generate_structured(
        self, prompt: str, schema: dict[str, Any]
    ) -> dict[str, Any]:
        raise LLMUnavailable("no LLM backend configured")
