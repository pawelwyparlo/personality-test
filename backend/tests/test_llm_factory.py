"""Factory tests: keyless -> NullClient, never an error at import/startup."""

from __future__ import annotations

from app.core.config import Settings
from app.llm import get_llm_client
from app.llm.null import NullClient


def test_keyless_yields_null_client():
    settings = Settings(
        google_cloud_project="",
        vertex_api_key="",
        google_application_credentials="",
    )
    client = get_llm_client(settings)
    assert isinstance(client, NullClient)


def test_project_without_credentials_stays_null():
    # A project alone is not enough to authenticate -> stay keyless.
    settings = Settings(
        google_cloud_project="my-proj",
        vertex_api_key="",
        google_application_credentials="",
    )
    assert isinstance(get_llm_client(settings), NullClient)


def test_construction_failure_degrades_to_null(monkeypatch):
    # An API key is present, but constructing the real client blows up; the
    # factory must degrade to NullClient rather than raise.
    import app.llm.factory as factory

    class Boom:
        def __init__(self, *a, **k):
            raise RuntimeError("no sdk")

    monkeypatch.setattr(factory, "_build", factory._build)  # keep real _build
    import app.llm.vertex as vertex

    monkeypatch.setattr(vertex, "VertexAIClient", Boom)
    settings = Settings(vertex_api_key="key-123")
    assert isinstance(get_llm_client(settings), NullClient)
