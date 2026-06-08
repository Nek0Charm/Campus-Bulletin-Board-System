from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, Index, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, IDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.board import Board
    from app.models.user import User


class BoardMaster(Base, IDMixin, TimestampMixin):
    __tablename__ = "board_masters"
    __table_args__ = (
        Index(
            "uq_board_masters_board_user",
            "board_id",
            "user_id",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )

    board_id: Mapped[UUID] = mapped_column(ForeignKey("boards.id"), nullable=False)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)

    board: Mapped["Board"] = relationship("Board", back_populates="board_masters")
    user: Mapped["User"] = relationship("User", back_populates="board_masters")
