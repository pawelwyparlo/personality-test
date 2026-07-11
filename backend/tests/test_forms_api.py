"""Tests for GET /api/v1/forms/{form}/items."""

from __future__ import annotations

import httpx
import pytest
from httpx import ASGITransport

from app.main import app


def _client() -> httpx.AsyncClient:
    return httpx.AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    )


@pytest.mark.asyncio
async def test_full_form_returns_120_items():
    async with _client() as client:
        resp = await client.get("/api/v1/forms/full/items")
    assert resp.status_code == 200
    body = resp.json()
    assert body["form"] == "full"
    assert body["count"] == 120
    assert len(body["items"]) == 120


@pytest.mark.asyncio
async def test_full_form_does_not_leak_keying_or_facet_internals():
    async with _client() as client:
        resp = await client.get("/api/v1/forms/full/items")
    items = resp.json()["items"]
    for it in items:
        assert set(it) == {"id", "text", "domain"}
        assert "keyed" not in it
        assert "facet" not in it


@pytest.mark.asyncio
async def test_quick_form_returns_501():
    async with _client() as client:
        resp = await client.get("/api/v1/forms/quick/items")
    assert resp.status_code == 501


@pytest.mark.asyncio
async def test_unknown_form_returns_404():
    async with _client() as client:
        resp = await client.get("/api/v1/forms/medium/items")
    assert resp.status_code == 404
