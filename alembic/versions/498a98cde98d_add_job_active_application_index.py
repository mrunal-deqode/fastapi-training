"""add job active application index

Revision ID: 498a98cde98d
Revises: f4576c00c624
Create Date: 2026-11-24 14:29:52.843503

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '498a98cde98d'
down_revision: Union[str, Sequence[str], None] = 'f4576c00c624'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "ix_applications_job_id_is_active",
        "applications",
        ["job_id", "is_active"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_applications_job_id_is_active",
        table_name="applications",
    )
