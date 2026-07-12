"""Report API tests (against a real Postgres, keyless -> text-bank narrative).

Covers: report body shape + descriptors, narrative persistence (stable across
requests), ``?regenerate=true``, the PDF endpoint (valid %PDF bytes, non-trivial
size), and 404s for missing / incomplete runs.
"""

from __future__ import annotations

import uuid

import pytest

pytestmark = pytest.mark.asyncio


async def _completed_run(client, age=30, sex="male") -> str:
    prof = await client.post("/api/v1/profiles")
    profile_id = prof.json()["id"]
    run = await client.post(
        "/api/v1/test-runs",
        json={"profile_id": profile_id, "form": "full", "age": age, "sex": sex},
    )
    run_id = run.json()["id"]
    for i in range(1, 121):
        resp = await client.post(
            f"/api/v1/test-runs/{run_id}/answers",
            json={"item_id": i, "value": ((i * 7) % 5) + 1},
        )
        assert resp.status_code == 204, resp.text
    done = await client.post(f"/api/v1/test-runs/{run_id}/complete")
    assert done.status_code == 200, done.text
    return run_id


async def _completed_quick_run(client, age=30, sex="female") -> str:
    prof = await client.post("/api/v1/profiles")
    profile_id = prof.json()["id"]
    run = await client.post(
        "/api/v1/test-runs",
        json={"profile_id": profile_id, "form": "quick", "age": age, "sex": sex},
    )
    run_id = run.json()["id"]
    for i in range(1, 61):
        resp = await client.post(
            f"/api/v1/test-runs/{run_id}/answers",
            json={"item_id": i, "value": ((i * 7) % 5) + 1},
        )
        assert resp.status_code == 204, resp.text
    done = await client.post(f"/api/v1/test-runs/{run_id}/complete")
    assert done.status_code == 200, done.text
    return run_id


async def test_report_body_shape(client):
    run_id = await _completed_run(client)
    resp = await client.get(f"/api/v1/reports/{run_id}")
    assert resp.status_code == 200, resp.text
    body = resp.json()

    assert body["run_id"] == run_id
    assert body["form"] == "full"
    assert body["completed_at"]
    assert len(body["domains"]) == 5
    assert len(body["facets"]) == 30
    for d in body["domains"]:
        assert {"domain", "name", "raw", "t_score", "percentile", "level"} <= set(d)

    narr = body["narrative"]
    # Keyless test env -> text-bank fallback.
    assert narr["source"] == "textbank"
    assert narr["pull_quote"]
    assert 2 <= len(narr["paragraphs"]) <= 4
    assert len(narr["strengths"]) == 3
    assert len(narr["watch_outs"]) == 3


async def test_narrative_persisted_and_stable(client):
    run_id = await _completed_run(client)
    first = (await client.get(f"/api/v1/reports/{run_id}")).json()["narrative"]
    second = (await client.get(f"/api/v1/reports/{run_id}")).json()["narrative"]
    assert first == second


async def test_regenerate_reruns_generation(client):
    run_id = await _completed_run(client)
    first = (await client.get(f"/api/v1/reports/{run_id}")).json()["narrative"]
    again = (
        await client.get(f"/api/v1/reports/{run_id}?regenerate=true")
    ).json()["narrative"]
    # Deterministic fallback -> identical content, but the path was exercised.
    assert again["source"] == "textbank"
    assert again == first


async def test_report_404_for_incomplete_run(client):
    prof = await client.post("/api/v1/profiles")
    profile_id = prof.json()["id"]
    run = await client.post(
        "/api/v1/test-runs",
        json={"profile_id": profile_id, "form": "full", "age": 30, "sex": "male"},
    )
    run_id = run.json()["id"]
    resp = await client.get(f"/api/v1/reports/{run_id}")
    assert resp.status_code == 404


async def test_report_404_for_missing_run(client):
    resp = await client.get(f"/api/v1/reports/{uuid.uuid4()}")
    assert resp.status_code == 404


async def test_pdf_endpoint_returns_valid_pdf(client):
    run_id = await _completed_run(client)
    resp = await client.get(f"/api/v1/reports/{run_id}/pdf")
    assert resp.status_code == 200, resp.text
    assert resp.headers["content-type"] == "application/pdf"
    assert "attachment" in resp.headers["content-disposition"]
    assert "bigfive-report-" in resp.headers["content-disposition"]
    body = resp.content
    assert body[:4] == b"%PDF"
    assert len(body) > 2000  # a real, non-trivial document


async def test_pdf_404_for_missing_run(client):
    resp = await client.get(f"/api/v1/reports/{uuid.uuid4()}/pdf")
    assert resp.status_code == 404


# --- Quick form: domain-only report + PDF (ADR-0004) ------------------------ #


async def test_quick_report_is_domain_only(client):
    """A Quick report carries 5 domains and NO facets, with a full narrative."""
    run_id = await _completed_quick_run(client)
    resp = await client.get(f"/api/v1/reports/{run_id}")
    assert resp.status_code == 200, resp.text
    body = resp.json()

    assert body["form"] == "quick"
    assert len(body["domains"]) == 5
    assert body["facets"] == []
    for d in body["domains"]:
        assert d["facets"] == []

    narr = body["narrative"]
    assert narr["source"] == "textbank"
    assert narr["pull_quote"]
    assert 2 <= len(narr["paragraphs"]) <= 4
    assert len(narr["strengths"]) == 3
    assert len(narr["watch_outs"]) == 3


async def test_quick_pdf_renders_from_facetless_run(client):
    """The PDF path handles a facetless (Quick) run and returns valid PDF bytes."""
    run_id = await _completed_quick_run(client)
    resp = await client.get(f"/api/v1/reports/{run_id}/pdf")
    assert resp.status_code == 200, resp.text
    assert resp.headers["content-type"] == "application/pdf"
    body = resp.content
    assert body[:4] == b"%PDF"
    assert len(body) > 2000
