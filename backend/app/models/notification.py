import enum
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import Boolean
from sqlalchemy import CheckConstraint
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Index
from sqlalchemy import String
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.models.base import Base
from app.models.base import IDMixin
from app.models.base import TimestampMixin
from app.models.user import User


class NotificationType(str, enum.Enum):
    COMMENT = "comment"
    REPLY = "reply"
    LIKE = "like"
    SYSTEM = "system"


class Notification(Base, IDMixin, TimestampMixin):
    __tablename__ = "notifications"
    __table_args__ = (
        CheckConstraint(
            "type IN ('comment', 'reply', 'like', 'system')",
            name="ck_notifications_type",
        ),
        Index("ix_notifications_recipient_id", "recipient_id"),
        Index(
            "ix_notifications_recipient_read_created",
            "recipient_id",
            "is_read",
            "created_at",
        ),
    )

    recipient_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    actor_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("users.id"))
    type: Mapped[str] = mapped_column(String(30), nullable=False)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    content: Mapped[str] = mapped_column(String(500), nullable=False)
    related_type: Mapped[Optional[str]] = mapped_column(String(20))
    related_id: Mapped[Optional[UUID]] = mapped_column(nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    recipient: Mapped[User] = relationship("User", foreign_keys=[recipient_id])
    actor: Mapped[Optional[User]] = relationship("User", foreign_keys=[actor_id])
