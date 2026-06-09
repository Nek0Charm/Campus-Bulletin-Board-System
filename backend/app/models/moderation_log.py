import enum
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import CheckConstraint
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Index
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy import func
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.models.base import Base
from app.models.base import IDMixin

if TYPE_CHECKING:
    from app.models.report import Report
    from app.models.user import User


class ModerationAction(str, enum.Enum):
    RESOLVE_REPORT = "resolve_report"
    DISMISS_REPORT = "dismiss_report"


class ModerationLog(Base, IDMixin):
    __tablename__ = "moderation_logs"
    __table_args__ = (
        CheckConstraint(
            "target_type IN ('post', 'comment')",
            name="ck_moderation_logs_target_type",
        ),
        CheckConstraint(
            "action IN ('resolve_report', 'dismiss_report')",
            name="ck_moderation_logs_action",
        ),
        Index("ix_moderation_logs_report_id", "report_id"),
        Index("ix_moderation_logs_operator_id", "operator_id"),
        Index("ix_moderation_logs_target", "target_type", "target_id"),
    )

    report_id: Mapped[UUID] = mapped_column(ForeignKey("reports.id"), nullable=False)
    operator_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    target_type: Mapped[str] = mapped_column(String(20), nullable=False)
    target_id: Mapped[UUID] = mapped_column(nullable=False)
    detail: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    report: Mapped["Report"] = relationship("Report")
    operator: Mapped["User"] = relationship("User")
