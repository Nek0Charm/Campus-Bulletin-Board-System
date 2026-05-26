import enum
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.board import Board

from uuid import UUID

from sqlalchemy import BigInteger, String, Text, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, IDMixin, TimestampMixin


class PostStatus(str, enum.Enum):
    NORMAL = "normal"
    HIDDEN = "hidden"
    DELETED = "deleted"


class Post(Base, IDMixin, TimestampMixin):
    __tablename__ = "posts"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    author_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    board_id: Mapped[UUID] = mapped_column(ForeignKey("boards.id"), nullable=False)

    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="normal", nullable=False)
    like_count: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)

    published_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.now, nullable=False
    )

    author: Mapped["User"] = relationship("User", back_populates="posts")
    board: Mapped["Board"] = relationship("Board", back_populates="posts")
