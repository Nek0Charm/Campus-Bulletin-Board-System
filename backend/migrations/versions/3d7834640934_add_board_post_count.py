"""add_board_post_count

Revision ID: 3d7834640934
Revises: d1f8a3b6e2c9
Create Date: 2026-06-09 11:03:52.920794

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "3d7834640934"
down_revision: Union[str, Sequence[str], None] = "d1f8a3b6e2c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "boards",
        sa.Column("post_count", sa.BigInteger(), nullable=False, server_default="0"),
    )
    op.alter_column("boards", "post_count", server_default=None)

    conn = op.get_bind()
    conn.execute(sa.text("""
        UPDATE boards
        SET post_count = (
            SELECT COUNT(*)
            FROM posts
            WHERE posts.board_id = boards.id
              AND posts.deleted_at IS NULL
              AND posts.status = 'normal'
        )
    """))


def downgrade() -> None:
    op.drop_column("boards", "post_count")
