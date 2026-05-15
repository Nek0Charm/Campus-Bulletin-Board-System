import enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.post import Post

from uuid import UUID

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, IDMixin, TimestampMixin


class CommentStatus(str, enum.Enum):
    NORMAL = "normal"
    HIDDEN = "hidden"
    DELETED = "deleted"


class Comment(Base, IDMixin, TimestampMixin):
    __tablename__ = "comments"
    __table_args__ = (
        CheckConstraint(
            "status IN ('normal', 'hidden', 'deleted')", name="ck_comments_status"
        ),
    )

    post_id: Mapped[UUID] = mapped_column(ForeignKey("posts.id"), nullable=False)
    author_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    parent_comment_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("comments.id"), nullable=True
    )
    root_comment_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("comments.id"), nullable=True
    )

    content: Mapped[str] = mapped_column(Text, nullable=False)

    status: Mapped[str] = mapped_column(String(20), default="normal", nullable=False)
    like_count: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    reply_count: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)

    author: Mapped["User"] = relationship("User")
    post: Mapped["Post"] = relationship("Post")
