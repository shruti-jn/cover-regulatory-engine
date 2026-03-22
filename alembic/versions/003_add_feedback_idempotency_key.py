"""
Add feedback idempotency key and uniqueness constraint.

Revision ID: 003
Revises: 002
Create Date: 2026-03-21 10:30:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("feedback", sa.Column("idempotency_key", sa.String(length=255), nullable=True))
    op.execute("UPDATE feedback SET idempotency_key = id::text WHERE idempotency_key IS NULL")
    op.alter_column("feedback", "idempotency_key", nullable=False)
    op.create_unique_constraint(
        "uq_feedback_assessment_idempotency_key",
        "feedback",
        ["assessment_id", "idempotency_key"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_feedback_assessment_idempotency_key", "feedback", type_="unique")
    op.drop_column("feedback", "idempotency_key")
