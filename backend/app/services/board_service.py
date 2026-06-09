from datetime import datetime, timezone
from typing import Optional, List
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.board import Board
from app.schemas.board import BoardCreate, BoardUpdate


class BoardService:
    def get_all(self, db: Session) -> List[Board]:
        boards = (
            db.query(Board)
            .filter(Board.deleted_at.is_(None))
            .order_by(Board.sort_order, Board.created_at)
            .all()
        )
        return boards

    def get_by_id(self, db: Session, id: UUID) -> Optional[Board]:
        board = (
            db.query(Board).filter(Board.id == id, Board.deleted_at.is_(None)).first()
        )
        return board

    def get_by_slug(self, db: Session, slug: str) -> Optional[Board]:
        board = (
            db.query(Board)
            .filter(Board.slug == slug, Board.deleted_at.is_(None))
            .first()
        )
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
