"""Report API (all under /api/v1).

Endpoints:
  GET /reports/{run_id}       -> the report body (scores + narrative)
  GET /reports/{run_id}/pdf   -> a WeasyPrint-rendered PDF download

The narrative is generated on first request and persisted on the TestRun
(``narrative`` JSONB), so later GETs return the same copy — stable across
reloads. ``?regenerate=true`` re-runs generation (useful after LLM keys are
added: a stored text-bank narrative can be refreshed to an LLM one).
"""

from __future__ import annotations

import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas import NarrativeOut, ReportOut
from app.core.db import get_session
from app.llm import get_llm_client
from app.models import RunStatus, TestRun
from app.report.narrative import generate_narrative
from app.report.pdf import render_report_pdf

router = APIRouter()


async def _completed_run(session: AsyncSession, run_id: uuid.UUID) -> TestRun:
    run = await session.get(TestRun, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="test run not found")
    if run.status != RunStatus.completed or run.scores is None:
        raise HTTPException(status_code=404, detail="test run is not completed")
    return run


async def _narrative_for(
    session: AsyncSession, run: TestRun, *, regenerate: bool
) -> dict:
    """Return the run's narrative, generating and persisting it if needed.

    Reuses the stored narrative unless it is missing or ``regenerate`` is set.
    Whatever is served is persisted (with its ``source``), so a keyless run
    stores the text-bank body and a later ``?regenerate=true`` (once keys exist)
    can upgrade it to an LLM one.
    """
    if run.narrative is not None and not regenerate:
        return run.narrative

    narrative = await generate_narrative(
        run.scores,
        age=run.age,
        sex=run.sex.value,
        form=run.form.value,
        llm=get_llm_client(),
    )
    run.narrative = narrative
    await session.commit()
    return narrative


@router.get("/reports/{run_id}")
async def get_report(
    run_id: uuid.UUID,
    regenerate: bool = Query(False),
    session: AsyncSession = Depends(get_session),
) -> ReportOut:
    run = await _completed_run(session, run_id)
    narrative = await _narrative_for(session, run, regenerate=regenerate)
    return ReportOut(
        run_id=run.id,
        form=run.form,
        completed_at=run.completed_at,
        domains=run.scores["domains"],
        facets=run.scores["facets"],
        narrative=NarrativeOut(**narrative),
    )


@router.get("/reports/{run_id}/pdf")
async def get_report_pdf(
    run_id: uuid.UUID,
    regenerate: bool = Query(False),
    session: AsyncSession = Depends(get_session),
) -> Response:
    run = await _completed_run(session, run_id)
    narrative = await _narrative_for(session, run, regenerate=regenerate)

    pdf_bytes = render_report_pdf(run.scores, narrative, form=run.form.value)
    filename = f"bigfive-report-{date.today().isoformat()}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
