"""coach schema: profiles.clerk_user_id, coaches, coach_messages

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-07-11 23:00:00.000000

Adds the Coach half of the product (PR5): an Account claim on a Profile
(``profiles.clerk_user_id``, nullable + unique per ADR-0002), the per-Profile
Coach (unique ``profile_id``), and its chat history (``coach_messages``).
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "c3d4e5f6a7b8"
down_revision: str | None = "b2c3d4e5f6a7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "profiles",
        sa.Column("clerk_user_id", sa.String(length=255), nullable=True),
    )
    op.create_index(
        "ix_profiles_clerk_user_id",
        "profiles",
        ["clerk_user_id"],
        unique=True,
    )

    op.create_table(
        "coaches",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("profile_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["profile_id"], ["profiles.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("profile_id", name="uq_coaches_profile_id"),
    )
    op.create_index(
        "ix_coaches_profile_id", "coaches", ["profile_id"], unique=True
    )

    op.create_table(
        "coach_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("coach_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "role",
            postgresql.ENUM("user", "coach", name="coach_role"),
            nullable=False,
        ),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["coach_id"], ["coaches.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_coach_messages_coach_id", "coach_messages", ["coach_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_coach_messages_coach_id", table_name="coach_messages")
    op.drop_table("coach_messages")
    op.drop_index("ix_coaches_profile_id", table_name="coaches")
    op.drop_table("coaches")
    op.drop_index("ix_profiles_clerk_user_id", table_name="profiles")
    op.drop_column("profiles", "clerk_user_id")
    op.execute("DROP TYPE IF EXISTS coach_role")
