"""create_reports_and_moderation_logs

Revision ID: 4f2a9c8d1b6e
Revises: 9fe49ab15048
Create Date: 2026-06-03 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "4f2a9c8d1b6e"
down_revision: Union[str, Sequence[str], None] = "9fe49ab15048"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "reports",
        sa.Column("reporter_id", sa.UUID(), nullable=False),
        sa.Column("target_type", sa.String(length=20), nullable=False),
        sa.Column("target_id", sa.UUID(), nullable=False),
        sa.Column("reason", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("handled_by", sa.UUID(), nullable=True),
        sa.Column("handled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("result_note", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.CheckConstraint(
            "target_type IN ('post', 'comment')", name="ck_reports_target_type"
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'resolved', 'dismissed')",
            name="ck_reports_status",
        ),
        sa.ForeignKeyConstraint(["handled_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["reporter_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_reports_reporter_id", "reports", ["reporter_id"])
    op.create_index("ix_reports_status", "reports", ["status"])
    op.create_index("ix_reports_target", "reports", ["target_type", "target_id"])

    op.create_table(
        "moderation_logs",
        sa.Column("report_id", sa.UUID(), nullable=False),
        sa.Column("operator_id", sa.UUID(), nullable=False),
        sa.Column("action", sa.String(length=50), nullable=False),
        sa.Column("target_type", sa.String(length=20), nullable=False),
        sa.Column("target_id", sa.UUID(), nullable=False),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.CheckConstraint(
            "target_type IN ('post', 'comment')",
            name="ck_moderation_logs_target_type",
        ),
        sa.CheckConstraint(
            "action IN ('resolve_report', 'dismiss_report')",
            name="ck_moderation_logs_action",
        ),
        sa.ForeignKeyConstraint(["operator_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["report_id"], ["reports.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_moderation_logs_operator_id", "moderation_logs", ["operator_id"]
    )
    op.create_index("ix_moderation_logs_report_id", "moderation_logs", ["report_id"])
    op.create_index(
        "ix_moderation_logs_target",
        "moderation_logs",
        ["target_type", "target_id"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_moderation_logs_target", table_name="moderation_logs")
    op.drop_index("ix_moderation_logs_report_id", table_name="moderation_logs")
    op.drop_index("ix_moderation_logs_operator_id", table_name="moderation_logs")
    op.drop_table("moderation_logs")
    op.drop_index("ix_reports_target", table_name="reports")
    op.drop_index("ix_reports_status", table_name="reports")
    op.drop_index("ix_reports_reporter_id", table_name="reports")
    op.drop_table("reports")
