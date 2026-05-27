from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, IDMixin


class PostLike(Base, IDMixin):
    __tablename__ = "post_likes"
    __table_args__ = (UniqueConstraint("post_id", "user_id", name="uq_post_likes"),)

    post_id: Mapped[UUID] = mapped_column(ForeignKey("posts.id"), nullable=False)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class CommentLike(Base, IDMixin):
    __tablename__ = "comment_likes"
    __table_args__ = (
        UniqueConstraint("comment_id", "user_id", name="uq_comment_likes"),
    )

    comment_id: Mapped[UUID] = mapped_column(ForeignKey("comments.id"), nullable=False)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
