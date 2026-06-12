from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.announcement import Announcement
from app.schemas.announcement import AnnouncementCreate, AnnouncementUpdate


class AnnouncementService:
    def list_published(self, db: Session) -> list[Announcement]:
        """返回已发布且在有效期内的公告，按创建时间降序。"""
        now = datetime.now(timezone.utc)
        return (
            db.query(Announcement)
            .filter(
                Announcement.deleted_at.is_(None),
                Announcement.is_published.is_(True),
                (Announcement.starts_at.is_(None) | (Announcement.starts_at <= now)),
                (Announcement.ends_at.is_(None) | (Announcement.ends_at >= now)),
            )
            .order_by(Announcement.created_at.desc())
            .all()
        )

    def list_all(self, db: Session) -> list[Announcement]:
        """管理端列表（包含未发布/已过期，按创建时间倒序）。"""
        return (
            db.query(Announcement)
            .filter(Announcement.deleted_at.is_(None))
            .order_by(Announcement.created_at.desc())
            .all()
        )

    def get_by_id(self, db: Session, id: UUID) -> Optional[Announcement]:
        return (
            db.query(Announcement)
            .filter(Announcement.id == id, Announcement.deleted_at.is_(None))
            .first()
        )

    def create(
        self, db: Session, *, obj_in: AnnouncementCreate, admin_id: UUID
    ) -> Announcement:
        db_obj = Announcement(**obj_in.model_dump(), created_by=admin_id)
        db.add(db_obj)
        try:
            db.commit()
        except Exception:
            db.rollback()
            raise
        db.refresh(db_obj)
        return db_obj

    def update(
        self, db: Session, *, db_obj: Announcement, obj_in: AnnouncementUpdate
    ) -> Announcement:
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

    def remove(self, db: Session, *, db_obj: Announcement) -> None:
        db_obj.deleted_at = datetime.now(timezone.utc)
        try:
            db.commit()
        except Exception:
            db.rollback()
            raise
