from datetime import datetime, timezone
from typing import List
from uuid import UUID

from sqlalchemy.orm import Session, joinedload

from app.models.board_master import BoardMaster


class BoardMasterService:
    def list_for_board(self, db: Session, board_id: UUID) -> List[BoardMaster]:
        return (
            db.query(BoardMaster)
            .options(joinedload(BoardMaster.user))
            .filter(
                BoardMaster.board_id == board_id,
                BoardMaster.deleted_at.is_(None),
            )
            .all()
        )

    def add(self, db: Session, *, board_id: UUID, user_id: UUID) -> BoardMaster:
        existing = (
            db.query(BoardMaster)
            .filter(
                BoardMaster.board_id == board_id,
                BoardMaster.user_id == user_id,
            )
            .first()
        )
        if existing:
            if existing.deleted_at is not None:
                existing.deleted_at = None
                existing.updated_at = datetime.now(timezone.utc)
                db.commit()
                db.refresh(existing)
            return existing

        db_obj = BoardMaster(board_id=board_id, user_id=user_id)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, *, board_id: UUID, user_id: UUID) -> None:
        record = (
            db.query(BoardMaster)
            .filter(
                BoardMaster.board_id == board_id,
                BoardMaster.user_id == user_id,
                BoardMaster.deleted_at.is_(None),
            )
            .first()
        )
        if record:
            record.deleted_at = datetime.now(timezone.utc)
            db.commit()

    def is_board_master(self, db: Session, *, board_id: UUID, user_id: UUID) -> bool:
        return (
            db.query(BoardMaster)
            .filter(
                BoardMaster.board_id == board_id,
                BoardMaster.user_id == user_id,
                BoardMaster.deleted_at.is_(None),
            )
            .first()
            is not None
        )

    def get_board_ids_for_user(self, db: Session, user_id: UUID) -> List[UUID]:
        records = (
            db.query(BoardMaster)
            .filter(
                BoardMaster.user_id == user_id,
                BoardMaster.deleted_at.is_(None),
            )
            .all()
        )
        return [r.board_id for r in records]
