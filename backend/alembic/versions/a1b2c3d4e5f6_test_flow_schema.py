"""test flow schema: profiles, test_runs, answers

Revision ID: a1b2c3d4e5f6
Revises: e72a84c0121a
Create Date: 2026-07-11 21:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: str | None = "e72a84c0121a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "test_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("profile_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "form",
            postgresql.ENUM("full", "quick", name="form"),
            nullable=False,
        ),
        sa.Column("age", sa.Integer(), nullable=False),
        sa.Column(
            "sex",
            postgresql.ENUM("male", "female", name="sex"),
            nullable=False,
        ),
        sa.Column(
            "status",
            postgresql.ENUM(
                "in_progress", "completed", "abandoned", name="run_status"
            ),
            nullable=False,
        ),
        sa.Column("scores", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "age >= 13 AND age <= 120", name="ck_test_runs_age_range"
        ),
        sa.ForeignKeyConstraint(
            ["profile_id"], ["profiles.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_test_runs_profile_id", "test_runs", ["profile_id"], unique=False
    )

    op.create_table(
        "answers",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("item_id", sa.Integer(), nullable=False),
        sa.Column("value", sa.Integer(), nullable=False),
        sa.Column(
            "answered_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "value >= 1 AND value <= 5", name="ck_answers_value_range"
        ),
        sa.ForeignKeyConstraint(
            ["run_id"], ["test_runs.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("run_id", "item_id", name="uq_answers_run_item"),
    )
    op.create_index("ix_answers_run_id", "answers", ["run_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_answers_run_id", table_name="answers")
    op.drop_table("answers")
    op.drop_index("ix_test_runs_profile_id", table_name="test_runs")
    op.drop_table("test_runs")
    op.drop_table("profiles")
    op.execute("DROP TYPE IF EXISTS run_status")
    op.execute("DROP TYPE IF EXISTS sex")
    op.execute("DROP TYPE IF EXISTS form")
