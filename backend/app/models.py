"""SQLAlchemy ORM models for the test-taking flow.

A :class:`Profile` is the anonymous identity everything hangs off (ADR-0002).
It owns many :class:`TestRun` rows; each run collects one :class:`Answer` per
Item of its Form. Answers are one-shot — no revisions, no gaps (ADR-0001) —
enforced by a unique constraint on ``(run_id, item_id)``.

Scores are persisted as JSONB on the run at completion (the full engine
``ScoreResult`` shape), so a completed run is self-contained and the report can
be re-rendered without re-scoring.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class Form(str, enum.Enum):
    full = "full"
    quick = "quick"


class Sex(str, enum.Enum):
    male = "male"
    female = "female"


class RunStatus(str, enum.Enum):
    in_progress = "in_progress"
    completed = "completed"
    abandoned = "abandoned"


class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    test_runs: Mapped[list[TestRun]] = relationship(
        back_populates="profile", cascade="all, delete-orphan"
    )


class TestRun(Base):
    __tablename__ = "test_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    form: Mapped[Form] = mapped_column(
        Enum(Form, name="form"), nullable=False
    )
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    sex: Mapped[Sex] = mapped_column(Enum(Sex, name="sex"), nullable=False)
    status: Mapped[RunStatus] = mapped_column(
        Enum(RunStatus, name="run_status"),
        nullable=False,
        default=RunStatus.in_progress,
    )
    # Full engine ScoreResult, persisted at completion; null until then.
    scores: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    # Generated report narrative (pull_quote/paragraphs/strengths/watch_outs/
    # source), written on first report request and reused thereafter so the copy
    # is stable across reloads. Null until the report is first requested.
    narrative: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    profile: Mapped[Profile] = relationship(back_populates="test_runs")
    answers: Mapped[list[Answer]] = relationship(
        back_populates="run", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint("age >= 13 AND age <= 120", name="ck_test_runs_age_range"),
    )


class Answer(Base):
    __tablename__ = "answers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("test_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    item_id: Mapped[int] = mapped_column(Integer, nullable=False)
    # Raw slider value 1..5; keying is applied by the engine at scoring time.
    value: Mapped[int] = mapped_column(Integer, nullable=False)
    answered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    run: Mapped[TestRun] = relationship(back_populates="answers")

    __table_args__ = (
        UniqueConstraint("run_id", "item_id", name="uq_answers_run_item"),
        CheckConstraint("value >= 1 AND value <= 5", name="ck_answers_value_range"),
    )
