from datetime import datetime, timezone
from typing import Optional, List
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.board import Board
from app.models.post import Post
from app.schemas.board import BoardCreate, BoardUpdate


def _attach_post_counts(db: Session, boards: list[Board]) -> None:
    """Attach post_count to each board via a single batch query."""
    if not boards:
        return
    board_ids = [b.id for b in boards]
    rows = (
        db.query(Post.board_id, func.count(Post.id))
        .filter(
            Post.board_id.in_(board_ids),
            Post.deleted_at.is_(None),
            Post.status == "normal",
        )
        .group_by(Post.board_id)
        .all()
    )
    counts = {row[0]: row[1] for row in rows}
    for b in boards:
        setattr(b, "post_count", counts.get(b.id, 0))


class BoardService:
    def get_all(self, db: Session) -> List[Board]:
        boards = (
            db.query(Board)
            .filter(Board.deleted_at.is_(None))
            .order_by(Board.sort_order, Board.created_at)
            .all()
        )
        _attach_post_counts(db, boards)
        return boards

    def get_by_id(self, db: Session, id: UUID) -> Optional[Board]:
        board = (
            db.query(Board).filter(Board.id == id, Board.deleted_at.is_(None)).first()
        )
        if board:
            _attach_post_counts(db, [board])
        return board

    def get_by_slug(self, db: Session, slug: str) -> Optional[Board]:
        board = (
            db.query(Board)
            .filter(Board.slug == slug, Board.deleted_at.is_(None))
            .first()
        )
        if board:
            _attach_post_counts(db, [board])
        return board

    def slug_exists(
        self, db: Session, slug: str, *, exclude_id: UUID | None = None
    ) -> bool:
        query = db.query(Board).filter(Board.slug == slug, Board.deleted_at.is_(None))
        if exclude_id is not None:
            query = query.filter(Board.id != exclude_id)
        return query.first() is not None

    def name_exists(
        self, db: Session, name: str, *, exclude_id: UUID | None = None
    ) -> bool:
        query = db.query(Board).filter(Board.name == name, Board.deleted_at.is_(None))
        if exclude_id is not None:
            query = query.filter(Board.id != exclude_id)
        return query.first() is not None

    def create(self, db: Session, *, obj_in: BoardCreate) -> Board:
        db_obj = Board(**obj_in.model_dump())
        db.add(db_obj)
        try:
            db.commit()
        except Exception:
            db.rollback()
            raise
        db.refresh(db_obj)
        return db_obj

    def update(self, db: Session, *, db_obj: Board, obj_in: BoardUpdate) -> Board:
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        if update_data:
            db_obj.updated_at = datetime.now(timezone.utc)
        try:
            db.commit()
        except Exception:
            db.rollback()
            raise
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, *, db_obj: Board) -> None:
        db_obj.deleted_at = datetime.now(timezone.utc)
        try:
            db.commit()
        except Exception:
            db.rollback()
            raise
