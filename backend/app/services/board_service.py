from datetime import datetime
from typing import Optional, List
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.board import Board
from app.schemas.board import BoardCreate, BoardUpdate


class BoardService:
    def get_all(self, db: Session) -> List[Board]:
        return (
            db.query(Board)
            .filter(Board.deleted_at.is_(None))
            .order_by(Board.sort_order, Board.created_at)
            .all()
        )

    def get_by_id(self, db: Session, id: UUID) -> Optional[Board]:
        return (
            db.query(Board).filter(Board.id == id, Board.deleted_at.is_(None)).first()
        )

    def get_by_slug(self, db: Session, slug: str) -> Optional[Board]:
        return (
            db.query(Board)
            .filter(Board.slug == slug, Board.deleted_at.is_(None))
            .first()
        )

    def create(self, db: Session, *, obj_in: BoardCreate) -> Board:
        db_obj = Board(**obj_in.model_dump())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(self, db: Session, *, db_obj: Board, obj_in: BoardUpdate) -> Board:
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db_obj.updated_at = datetime.now()
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, *, db_obj: Board) -> None:
        db_obj.deleted_at = datetime.now()
        db.commit()
