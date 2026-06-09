"""merge_heads

Revision ID: 5b0af807c62a
Revises: 4a2e8f1b3c6d, 5f6a7b8c9d10
Create Date: 2026-06-08 15:48:25.808814

"""

from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "5b0af807c62a"
down_revision: Union[str, Sequence[str], None] = ("4a2e8f1b3c6d", "5f6a7b8c9d10")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
