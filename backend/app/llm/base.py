"""LLM client protocol and shared error type (ADR-0003).

The interface is deliberately minimal: one async structured-output call. The
coach (a later PR) will add a streaming chat method to the same protocol; the
report only needs :meth:`generate_structured`.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


class LLMUnavailable(RuntimeError):
    """Raised when no LLM is configured or a generation call fails.

    Callers are expected to catch this and fall back (the report renders from
    the deterministic text bank). It is never raised at import or app startup —
    only when a generation is actually attempted without a working backend.
    """


@runtime_checkable
class LLMClient(Protocol):
    """A thin structured-output client.

    Implementations must be safe to construct without a configured backend; the
    failure surfaces only when :meth:`generate_structured` is called.
    """

    async def generate_structured(
        self, prompt: str, schema: dict[str, Any]
    ) -> dict[str, Any]:
        """Generate a JSON object conforming to ``schema`` from ``prompt``.

        ``schema`` is a JSON-Schema-style ``object`` definition. Returns the
        parsed object. Raises :class:`LLMUnavailable` if generation cannot be
        performed (no backend) or fails (network/parse error).
        """
        ...
