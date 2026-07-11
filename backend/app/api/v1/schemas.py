"""Request/response models for the test-run API (all /api/v1)."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, Field

from app.models import Form, RunStatus, Sex


class ProfileCreated(BaseModel):
    id: uuid.UUID


class TestRunCreate(BaseModel):
    profile_id: uuid.UUID
    form: Form
    age: int = Field(ge=13, le=120)
    sex: Sex


class TestRunCreated(BaseModel):
    id: uuid.UUID
    item_count: int


class AnswerCreate(BaseModel):
    item_id: int
    value: int = Field(ge=1, le=5)


class FacetScoreOut(BaseModel):
    domain: str
    number: int
    name: str
    raw: int
    t_score: float
    percentile: int
    level: str


class DomainScoreOut(BaseModel):
    domain: str
    name: str
    raw: int
    t_score: float
    percentile: int
    level: str
    facets: list[FacetScoreOut]


class ScoreResultOut(BaseModel):
    """The full scored result of a completed run.

    ``domains`` and ``facets`` are flattened lists (facets carry a ``domain``
    letter) so the client can render either grouping without re-deriving order.
    """

    run_id: uuid.UUID
    age: int
    sex: str
    domains: list[DomainScoreOut]
    facets: list[FacetScoreOut]


class TestRunStatus(BaseModel):
    id: uuid.UUID
    status: RunStatus
    form: Form
    item_count: int
    answered_count: int
    scores: ScoreResultOut | None = None
