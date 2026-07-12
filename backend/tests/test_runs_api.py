"""API-level tests for the test-run lifecycle.

These exercise the real endpoints against a real Postgres (see conftest).
Happy path answers all 120 items via the API and asserts the completed scores
match the pure engine's output for the same answers/demographics.
"""

from __future__ import annotations

import pytest

from app.scoring.engine import score
from app.scoring.engine_quick import score as score_quick
from app.scoring.serialize import score_result_to_dict

pytestmark = pytest.mark.asyncio


async def _new_run(client, age=30, sex="male", form="full"):
    prof = await client.post("/api/v1/profiles")
    assert prof.status_code == 201
    profile_id = prof.json()["id"]

    run = await client.post(
        "/api/v1/test-runs",
        json={"profile_id": profile_id, "form": form, "age": age, "sex": sex},
    )
    assert run.status_code == 201
    return run.json()["id"]


async def test_create_profile_and_run(client):
    run_id = await _new_run(client)
    assert run_id

    got = await client.get(f"/api/v1/test-runs/{run_id}")
    assert got.status_code == 200
    body = got.json()
    assert body["status"] == "in_progress"
    assert body["item_count"] == 120
    assert body["answered_count"] == 0
    assert body["scores"] is None


async def test_quick_run_reports_item_count_60(client):
    prof = await client.post("/api/v1/profiles")
    profile_id = prof.json()["id"]
    run = await client.post(
        "/api/v1/test-runs",
        json={"profile_id": profile_id, "form": "quick", "age": 30, "sex": "male"},
    )
    assert run.status_code == 201
    assert run.json()["item_count"] == 60

    got = await client.get(f"/api/v1/test-runs/{run.json()['id']}")
    assert got.json()["item_count"] == 60


async def test_quick_run_happy_path_matches_engine(client):
    """A full Quick run scores domain-only, matching the pure quick engine."""
    age, sex = 30, "female"
    prof = await client.post("/api/v1/profiles")
    profile_id = prof.json()["id"]
    run = await client.post(
        "/api/v1/test-runs",
        json={"profile_id": profile_id, "form": "quick", "age": age, "sex": sex},
    )
    run_id = run.json()["id"]

    answers = {i: ((i * 7) % 5) + 1 for i in range(1, 61)}
    for item_id, value in answers.items():
        resp = await client.post(
            f"/api/v1/test-runs/{run_id}/answers",
            json={"item_id": item_id, "value": value},
        )
        assert resp.status_code == 204, resp.text

    resp = await client.post(f"/api/v1/test-runs/{run_id}/complete")
    assert resp.status_code == 200, resp.text
    body = resp.json()

    expected = score_result_to_dict(score_quick(answers, age, sex), run_id)
    assert body["domains"] == expected["domains"]
    assert len(body["domains"]) == 5
    # Domain-only (ADR-0004): no facets are ever produced on a Quick run.
    assert body["facets"] == []
    for d in body["domains"]:
        assert d["facets"] == []


async def test_quick_run_rejects_full_only_item(client):
    """Item ids past 60 are unknown to the Quick form (60 items only)."""
    prof = await client.post("/api/v1/profiles")
    profile_id = prof.json()["id"]
    run = await client.post(
        "/api/v1/test-runs",
        json={"profile_id": profile_id, "form": "quick", "age": 30, "sex": "male"},
    )
    run_id = run.json()["id"]
    resp = await client.post(
        f"/api/v1/test-runs/{run_id}/answers",
        json={"item_id": 61, "value": 3},
    )
    assert resp.status_code == 422


async def test_age_out_of_range_rejected(client):
    prof = await client.post("/api/v1/profiles")
    profile_id = prof.json()["id"]
    run = await client.post(
        "/api/v1/test-runs",
        json={"profile_id": profile_id, "form": "full", "age": 5, "sex": "male"},
    )
    assert run.status_code == 422


async def test_full_run_happy_path_matches_engine(client):
    age, sex = 30, "male"
    run_id = await _new_run(client, age=age, sex=sex)

    # A deterministic answer pattern across the 1..5 scale.
    answers = {i: ((i * 7) % 5) + 1 for i in range(1, 121)}
    for item_id, value in answers.items():
        resp = await client.post(
            f"/api/v1/test-runs/{run_id}/answers",
            json={"item_id": item_id, "value": value},
        )
        assert resp.status_code == 204, resp.text

    resp = await client.post(f"/api/v1/test-runs/{run_id}/complete")
    assert resp.status_code == 200, resp.text
    body = resp.json()

    expected = score_result_to_dict(score(answers, age, sex), run_id)
    assert body["domains"] == expected["domains"]
    assert body["facets"] == expected["facets"]
    assert len(body["domains"]) == 5
    assert len(body["facets"]) == 30

    # GET now returns completed status with the stored scores.
    got = await client.get(f"/api/v1/test-runs/{run_id}")
    assert got.json()["status"] == "completed"
    assert got.json()["scores"]["domains"] == expected["domains"]


async def test_duplicate_answer_conflicts(client):
    run_id = await _new_run(client)
    first = await client.post(
        f"/api/v1/test-runs/{run_id}/answers",
        json={"item_id": 1, "value": 3},
    )
    assert first.status_code == 204
    dup = await client.post(
        f"/api/v1/test-runs/{run_id}/answers",
        json={"item_id": 1, "value": 5},
    )
    assert dup.status_code == 409


async def test_unknown_item_rejected(client):
    run_id = await _new_run(client)
    resp = await client.post(
        f"/api/v1/test-runs/{run_id}/answers",
        json={"item_id": 999, "value": 3},
    )
    assert resp.status_code == 422


async def test_complete_incomplete_run_rejected(client):
    run_id = await _new_run(client)
    await client.post(
        f"/api/v1/test-runs/{run_id}/answers",
        json={"item_id": 1, "value": 3},
    )
    resp = await client.post(f"/api/v1/test-runs/{run_id}/complete")
    assert resp.status_code == 422


async def test_abandon_is_idempotent_and_blocks_answers(client):
    run_id = await _new_run(client)
    first = await client.post(f"/api/v1/test-runs/{run_id}/abandon")
    assert first.status_code == 200
    assert first.json()["status"] == "abandoned"

    again = await client.post(f"/api/v1/test-runs/{run_id}/abandon")
    assert again.status_code == 200
    assert again.json()["status"] == "abandoned"

    # Answers rejected once abandoned.
    resp = await client.post(
        f"/api/v1/test-runs/{run_id}/answers",
        json={"item_id": 1, "value": 3},
    )
    assert resp.status_code == 409


async def test_answer_on_missing_run_404(client):
    import uuid

    resp = await client.post(
        f"/api/v1/test-runs/{uuid.uuid4()}/answers",
        json={"item_id": 1, "value": 3},
    )
    assert resp.status_code == 404
