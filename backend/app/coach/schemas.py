"""Request/response models for the Coach API (all /api/v1)."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models import CoachRole


class CoachCreate(BaseModel):
    profile_id: uuid.UUID


class CoachCreated(BaseModel):
    id: uuid.UUID
    name: str


class CoachMessageOut(BaseModel):
    id: uuid.UUID
    role: CoachRole
    content: str
    created_at: datetime


class TraitContextOut(BaseModel):
    """The latest completed run's five domain percentiles, for the header line.

    ``run_id`` is the run these traits come from, so the client can link "My
    report" to the right report.
    """

    run_id: uuid.UUID
    percentiles: dict[str, int]  # keyed by domain letter (O/C/E/A/N)


class CoachOut(BaseModel):
    id: uuid.UUID
    name: str
    messages: list[CoachMessageOut]
    trait_context: TraitContextOut


class CoachMessageCreate(BaseModel):
    content: str
