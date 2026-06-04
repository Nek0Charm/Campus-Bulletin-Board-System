from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import BigInteger
from sqlalchemy import Boolean
from sqlalchemy import CheckConstraint
from sqlalchemy import CHAR
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Index
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import func
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.models.base import Base
from app.models.base import IDMixin
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.post import Post
    from app.models.user import User


class MediaAsset(Base, IDMixin, TimestampMixin):
    __tablename__ = "media_assets"
    __table_args__ = (
        CheckConstraint(
            "source_type IN ('post', 'comment', 'avatar')",
            name="ck_media_source_type",
        ),
        Index(
            "uq_media_bucket_object_key",
            "bucket",
            "object_key",
            unique=True,
        ),
    )

    uploader_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    bucket: Mapped[str] = mapped_column(String(100), nullable=False)
    object_key: Mapped[str] = mapped_column(String(512), nullable=False)
    url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sha256: Mapped[str | None] = mapped_column(CHAR(64), nullable=True)
    source_type: Mapped[str] = mapped_column(String(20), nullable=False)
    source_id: Mapped[UUID | None] = mapped_column(nullable=True)
    is_public: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    uploader: Mapped["User"] = relationship("User")


class PostAttachment(Base, IDMixin):
    __tablename__ = "post_attachments"

    post_id: Mapped[UUID] = mapped_column(ForeignKey("posts.id"), nullable=False)
    media_id: Mapped[UUID] = mapped_column(
        ForeignKey("media_assets.id"), nullable=False
    )
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    post: Mapped["Post"] = relationship("Post")
    media: Mapped[MediaAsset] = relationship("MediaAsset")
