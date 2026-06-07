"""add_post_search_index

Revision ID: 5f6a7b8c9d10
Revises: c12e790a4df5
Create Date: 2026-06-06 15:30:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "5f6a7b8c9d10"
down_revision: Union[str, Sequence[str], None] = "c12e790a4df5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "posts",
        sa.Column("search_document", sa.Text(), nullable=False, server_default=""),
    )
    op.add_column(
        "posts",
        sa.Column("search_vector", postgresql.TSVECTOR(), nullable=True),
    )

    op.execute(
        """
        CREATE OR REPLACE FUNCTION posts_search_vector_refresh()
        RETURNS trigger AS $$
        BEGIN
            NEW.search_vector :=
                to_tsvector('simple', COALESCE(NEW.search_document, ''));
            RETURN NEW;
        END
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_posts_search_vector_refresh
        BEFORE INSERT OR UPDATE OF search_document ON posts
        FOR EACH ROW EXECUTE FUNCTION posts_search_vector_refresh();
        """
    )
    op.execute(
        """
        UPDATE posts
        SET search_document =
            COALESCE(title, '') || ' ' || COALESCE(content, '')
        """
    )

    op.create_index(
        "ix_posts_search_vector",
        "posts",
        ["search_vector"],
        postgresql_using="gin",
        postgresql_where=sa.text("deleted_at IS NULL AND status = 'normal'"),
    )
    op.create_index(
        "ix_posts_search_filters",
        "posts",
        ["board_id", "published_at"],
    )
    op.alter_column("posts", "search_document", server_default=None)


def downgrade() -> None:
    op.drop_index("ix_posts_search_filters", table_name="posts")
    op.drop_index("ix_posts_search_vector", table_name="posts")
    op.execute("DROP TRIGGER IF EXISTS trg_posts_search_vector_refresh ON posts")
    op.execute("DROP FUNCTION IF EXISTS posts_search_vector_refresh")
    op.drop_column("posts", "search_vector")
    op.drop_column("posts", "search_document")

