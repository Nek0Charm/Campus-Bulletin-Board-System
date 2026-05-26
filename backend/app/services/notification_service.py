from datetime import datetime
from datetime import timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import asc
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.notification import Notification


class NotificationService:
    def create(
        self,
        db: Session,
        *,
        recipient_id: UUID,
        actor_id: UUID | None = None,
        type: str,
        title: str,
        content: str,
        related_type: str | None = None,
        related_id: UUID | None = None,
    ) -> Notification:
        db_obj = Notification(
            recipient_id=recipient_id,
            actor_id=actor_id,
            type=type,
            title=title,
            content=content,
            related_type=related_type,
            related_id=related_id,
        )
        db.add(db_obj)
        try:
            db.commit()
        except Exception:
            db.rollback()
            raise
        db.refresh(db_obj)
        return db_obj

    def list_for_user(
        self,
        db: Session,
        *,
        user_id: UUID,
        page: int = 1,
        page_size: int = 20,
        unread_only: bool = False,
    ) -> tuple[list[Notification], int]:
        query = db.query(Notification).filter(
            Notification.recipient_id == user_id,
            Notification.deleted_at.is_(None),
        )
        if unread_only:
            query = query.filter(Notification.is_read.is_(False))

        query = query.order_by(
            asc(Notification.is_read),
            desc(Notification.created_at),
            desc(Notification.id),
        )
        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()
        return items, total

    def get_for_user(
        self, db: Session, *, notification_id: UUID, user_id: UUID
    ) -> Optional[Notification]:
        return (
            db.query(Notification)
            .filter(
                Notification.id == notification_id,
                Notification.recipient_id == user_id,
                Notification.deleted_at.is_(None),
            )
            .first()
        )

    def get_unread_count(self, db: Session, *, user_id: UUID) -> int:
        return (
            db.query(Notification)
            .filter(
                Notification.recipient_id == user_id,
                Notification.is_read.is_(False),
                Notification.deleted_at.is_(None),
            )
            .count()
        )

    def mark_read(self, db: Session, *, db_obj: Notification) -> Notification:
        if not db_obj.is_read:
            now = datetime.now(timezone.utc)
            db_obj.is_read = True
            db_obj.read_at = now
            db_obj.updated_at = now
            try:
                db.commit()
            except Exception:
                db.rollback()
                raise
            db.refresh(db_obj)
        return db_obj

    def mark_all_read(self, db: Session, *, user_id: UUID) -> int:
        notifications = (
            db.query(Notification)
            .filter(
                Notification.recipient_id == user_id,
                Notification.is_read.is_(False),
                Notification.deleted_at.is_(None),
            )
            .all()
        )
        if not notifications:
            return 0

        now = datetime.now(timezone.utc)
        for notification in notifications:
            notification.is_read = True
            notification.read_at = now
            notification.updated_at = now

        try:
            db.commit()
        except Exception:
            db.rollback()
            raise
        return len(notifications)
