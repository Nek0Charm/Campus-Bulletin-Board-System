"""fix_announcements_updated_at_not_null

Revision ID: e90bbe2aa2a4
Revises: 3d7834640934
Create Date: 2026-06-12 20:25:43.172293

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "e90bbe2aa2a4"
down_revision: Union[str, Sequence[str], None] = "3d7834640934"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Fill existing NULLs before setting NOT NULL
    op.execute("UPDATE announcements SET updated_at = now() WHERE updated_at IS NULL")
    op.alter_column(
        "announcements",
        "updated_at",
        existing_type=postgresql.TIMESTAMP(timezone=True),
        server_default=sa.text("now()"),
        nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "announcements",
        "updated_at",
        existing_type=postgresql.TIMESTAMP(timezone=True),
        server_default=None,
        nullable=True,
    )
