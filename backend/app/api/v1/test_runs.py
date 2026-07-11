"""Test-run lifecycle API (all under /api/v1).

Endpoints:
  POST /profiles                     -> issue an anonymous Profile
  POST /test-runs                    -> start a run for a Profile + Form
  POST /test-runs/{id}/answers       -> commit one one-shot Answer
  POST /test-runs/{id}/complete      -> score a fully-answered run
  POST /test-runs/{id}/abandon       -> abandon a run (idempotent)
  GET  /test-runs/{id}               -> status (+ scores if completed)

Answers are one-shot (ADR-0001): a duplicate ``(run_id, item_id)`` is a 409, not
an overwrite. Completion requires every Item of the Form to be answered.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas import (
    AnswerCreate,
    ProfileCreated,
    ScoreResultOut,
    TestRunCreate,
    TestRunCreated,
    TestRunStatus,
)
from app.core.db import get_session
from app.models import Answer, Form, Profile, RunStatus, TestRun
from app.scoring import forms
from app.scoring.engine import score
from app.scoring.serialize import score_result_to_dict

router = APIRouter()


async def _get_run(session: AsyncSession, run_id: uuid.UUID) -> TestRun:
    run = await session.get(TestRun, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="test run not found")
    return run


@router.post("/profiles", status_code=201)
async def create_profile(
    session: AsyncSession = Depends(get_session),
) -> ProfileCreated:
    """Issue a fresh anonymous Profile (no body needed)."""
    profile = Profile()
    session.add(profile)
    await session.commit()
    return ProfileCreated(id=profile.id)


@router.post("/test-runs", status_code=201)
async def create_test_run(
    payload: TestRunCreate,
    session: AsyncSession = Depends(get_session),
) -> TestRunCreated:
    """Start a Test Run. Quick is not implemented yet (ADR-0004) -> 501."""
    if payload.form == Form.quick:
        raise HTTPException(status_code=501, detail="Quick form coming soon")

    profile = await session.get(Profile, payload.profile_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="profile not found")

    run = TestRun(
        profile_id=payload.profile_id,
        form=payload.form,
        age=payload.age,
        sex=payload.sex,
        status=RunStatus.in_progress,
    )
    session.add(run)
    await session.commit()
    return TestRunCreated(id=run.id, item_count=forms.item_count(payload.form.value))


@router.post("/test-runs/{run_id}/answers", status_code=204)
async def create_answer(
    run_id: uuid.UUID,
    payload: AnswerCreate,
    session: AsyncSession = Depends(get_session),
) -> Response:
    """Commit one Answer. One-shot: duplicate item -> 409 (ADR-0001)."""
    run = await _get_run(session, run_id)
    if run.status != RunStatus.in_progress:
        raise HTTPException(status_code=409, detail="test run is not in progress")

    valid_ids = forms.item_ids(run.form.value)
    if payload.item_id not in valid_ids:
        raise HTTPException(
            status_code=422, detail=f"unknown item for form: {payload.item_id}"
        )

    existing = await session.scalar(
        select(Answer).where(
            Answer.run_id == run_id, Answer.item_id == payload.item_id
        )
    )
    if existing is not None:
        raise HTTPException(status_code=409, detail="item already answered")

    session.add(
        Answer(run_id=run_id, item_id=payload.item_id, value=payload.value)
    )
    await session.commit()
    return Response(status_code=204)


@router.post("/test-runs/{run_id}/complete")
async def complete_test_run(
    run_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> ScoreResultOut:
    """Score a fully-answered run; persist scores and mark completed."""
    run = await _get_run(session, run_id)

    if run.status == RunStatus.completed and run.scores is not None:
        # Idempotent-ish: re-completing a completed run returns its stored scores.
        return ScoreResultOut(**run.scores)
    if run.status != RunStatus.in_progress:
        raise HTTPException(status_code=409, detail="test run is not in progress")

    rows = await session.execute(
        select(Answer.item_id, Answer.value).where(Answer.run_id == run_id)
    )
    answers = {item_id: value for item_id, value in rows.all()}

    expected = forms.item_ids(run.form.value)
    if set(answers) != set(expected):
        missing = len(expected) - len(set(answers) & set(expected))
        raise HTTPException(
            status_code=422,
            detail=f"run is incomplete: {missing} of {len(expected)} items unanswered",
        )

    result = score(answers, run.age, run.sex.value)
    scores_dict = score_result_to_dict(result, str(run_id))

    run.scores = scores_dict
    run.status = RunStatus.completed
    run.completed_at = datetime.now(timezone.utc)
    await session.commit()

    return ScoreResultOut(**scores_dict)


@router.post("/test-runs/{run_id}/abandon", status_code=200)
async def abandon_test_run(
    run_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Abandon a run. Idempotent; completed runs are left untouched."""
    run = await _get_run(session, run_id)
    if run.status == RunStatus.in_progress:
        run.status = RunStatus.abandoned
        await session.commit()
    return {"id": str(run.id), "status": run.status.value}


@router.get("/test-runs/{run_id}")
async def get_test_run(
    run_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> TestRunStatus:
    """Return run status plus scores if the run is completed."""
    run = await _get_run(session, run_id)
    answered_count = await session.scalar(
        select(func.count()).select_from(Answer).where(Answer.run_id == run_id)
    )
    scores = ScoreResultOut(**run.scores) if run.scores is not None else None
    return TestRunStatus(
        id=run.id,
        status=run.status,
        form=run.form,
        item_count=forms.item_count(run.form.value),
        answered_count=answered_count or 0,
        scores=scores,
    )
