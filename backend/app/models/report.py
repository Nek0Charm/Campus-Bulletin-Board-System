import enum
from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import CheckConstraint
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Index
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.models.base import Base
from app.models.base import IDMixin
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User


class ReportTargetType(str, enum.Enum):
    POST = "post"
    COMMENT = "comment"


class ReportStatus(str, enum.Enum):
    PENDING = "pending"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class Report(Base, IDMixin, TimestampMixin):
    __tablename__ = "reports"
    __table_args__ = (
        CheckConstraint(
            "target_type IN ('post', 'comment')", name="ck_reports_target_type"
        ),
        CheckConstraint(
            "status IN ('pending', 'resolved', 'dismissed')",
            name="ck_reports_status",
        ),
        Index("ix_reports_status", "status"),
        Index("ix_reports_reporter_id", "reporter_id"),
        Index("ix_reports_target", "target_type", "target_id"),
    )

    reporter_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    target_type: Mapped[str] = mapped_column(String(20), nullable=False)
    target_id: Mapped[UUID] = mapped_column(nullable=False)
    reason: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default=ReportStatus.PENDING.value, nullable=False
    )
    handled_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    handled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    result_note: Mapped[str | None] = mapped_column(Text)

    reporter: Mapped["User"] = relationship("User", foreign_keys=[reporter_id])
    handler: Mapped[Optional["User"]] = relationship("User", foreign_keys=[handled_by])
