"""LLM client factory — reads settings, never raises at import/startup.

The single rule from ADR-0003: **no key configured -> NullClient, never an
error**. A Vertex client is only constructed when the environment carries enough
to authenticate — either an API key, or a project plus service-account
credentials. Any failure while constructing the real client degrades to the null
client rather than propagating, so a misconfigured key can't take the app down;
the report simply falls back to the text bank.
"""

from __future__ import annotations

from app.core.config import Settings, get_settings
from app.llm.base import LLMClient
from app.llm.null import NullClient


def _build(settings: Settings) -> LLMClient:
    api_key = settings.vertex_api_key.strip()
    project = settings.google_cloud_project.strip()
    creds = settings.google_application_credentials.strip()

    # Need at least one usable auth path; otherwise stay keyless.
    if not api_key and not (project and creds):
        return NullClient()

    try:
        from app.llm.vertex import VertexAIClient

        return VertexAIClient(
            model=settings.vertex_model,
            project=project,
            location=settings.vertex_location,
            api_key=api_key,
        )
    except Exception:  # pragma: no cover - degrade rather than crash startup
        return NullClient()


def get_llm_client(settings: Settings | None = None) -> LLMClient:
    """Return the configured LLM client (or a :class:`NullClient` if keyless)."""
    return _build(settings or get_settings())
