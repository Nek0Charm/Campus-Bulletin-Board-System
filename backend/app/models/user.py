from datetime import datetime
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from app.models.post import Post
    from app.models.board_master import BoardMaster

from sqlalchemy import Boolean
from sqlalchemy import CheckConstraint
from sqlalchemy import DateTime
from sqlalchemy import Index
from sqlalchemy import String
from sqlalchemy import text
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.models.base import Base
from app.models.base import IDMixin
from app.models.base import TimestampMixin


class User(Base, IDMixin, TimestampMixin):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("role IN ('user', 'admin')", name="ck_users_role"),
        CheckConstraint(
            "status IN ('active', 'inactive', 'banned')", name="ck_users_status"
        ),
        Index(
            "uq_users_username",
            "username",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
        Index(
            "uq_users_email",
            "email",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )

    username: Mapped[str] = mapped_column(String(32), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    nickname: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    # 昵称是对外展示给其他用户看的，可以为空
    avatar_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="user")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    email_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    muted_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    posts: Mapped[list["Post"]] = relationship("Post", back_populates="author")
    board_masters: Mapped[list["BoardMaster"]] = relationship(
        "BoardMaster", back_populates="user"
    )
