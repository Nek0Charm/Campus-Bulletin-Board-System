from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from app.models.post import Post

from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, IDMixin, TimestampMixin


class Board(Base, IDMixin, TimestampMixin):
    __tablename__ = "boards"

    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)

    slug: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)

    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    posts: Mapped[list["Post"]] = relationship("Post", back_populates="board")
