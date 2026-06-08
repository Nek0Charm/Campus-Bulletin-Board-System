"""merge heads

Revision ID: d93f4286e1c0
Revises: d1f8a3b6e2c9, 4a2e8f1b3c6d, 5f6a7b8c9d10
Create Date: 2026-06-08 16:38:25.206595

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "d93f4286e1c0"
down_revision: Union[str, Sequence[str], None] = (
    "d1f8a3b6e2c9",
    "4a2e8f1b3c6d",
    "5f6a7b8c9d10",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
