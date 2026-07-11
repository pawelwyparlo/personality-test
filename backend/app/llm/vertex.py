"""Vertex AI implementation of :class:`~app.llm.base.LLMClient`.

Wraps the ``google-genai`` SDK in Vertex mode. All configuration comes from the
environment (never hardcoded): the client is created for a project/location and
authenticates via either a service-account credentials file
(``GOOGLE_APPLICATION_CREDENTIALS``, picked up by the SDK's default credentials)
or an API key. The model id is configurable (``VERTEX_MODEL``), defaulting to a
current Gemini flash model.

The import of ``google-genai`` is lazy (inside ``__init__``) so the package is an
optional dependency: a keyless deployment that never constructs this client does
not need the SDK installed, and nothing fails at app import time.
"""

from __future__ import annotations

import json
from typing import Any

from app.llm.base import LLMUnavailable


class VertexAIClient:
    """Structured-output client backed by Vertex AI (google-genai)."""

    def __init__(
        self,
        *,
        model: str,
        project: str = "",
        location: str = "us-central1",
        api_key: str = "",
    ) -> None:
        try:
            from google import genai
        except ImportError as exc:  # pragma: no cover - depends on env
            raise LLMUnavailable(
                "google-genai is not installed; cannot use Vertex AI"
            ) from exc

        self._model = model
        try:
            if api_key:
                # API-key auth against Vertex (Express mode / API key).
                self._client = genai.Client(vertexai=True, api_key=api_key)
            else:
                # Application Default Credentials — including a service-account
                # file pointed to by GOOGLE_APPLICATION_CREDENTIALS.
                self._client = genai.Client(
                    vertexai=True, project=project, location=location
                )
        except Exception as exc:  # pragma: no cover - depends on env
            raise LLMUnavailable(f"failed to initialise Vertex AI client: {exc}") from exc

    async def generate_structured(
        self, prompt: str, schema: dict[str, Any]
    ) -> dict[str, Any]:
        from google.genai import types

        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=schema,
        )
        try:
            response = await self._client.aio.models.generate_content(
                model=self._model,
                contents=prompt,
                config=config,
            )
        except Exception as exc:
            raise LLMUnavailable(f"Vertex AI generation failed: {exc}") from exc

        text = getattr(response, "text", None)
        if not text:
            raise LLMUnavailable("Vertex AI returned an empty response")
        try:
            parsed = json.loads(text)
        except (ValueError, TypeError) as exc:
            raise LLMUnavailable(f"Vertex AI returned non-JSON output: {exc}") from exc
        if not isinstance(parsed, dict):
            raise LLMUnavailable("Vertex AI returned a non-object JSON value")
        return parsed
