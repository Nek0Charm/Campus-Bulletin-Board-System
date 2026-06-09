from uuid import UUID

from sqlalchemy.orm import Session

from app.models.moderation_log import ModerationLog


class ModerationService:
    def create_log(
        self,
        db: Session,
        *,
        report_id: UUID,
        operator_id: UUID,
        action: str,
        target_type: str,
        target_id: UUID,
        detail: str | None = None,
    ) -> ModerationLog:
        db_obj = ModerationLog(
            report_id=report_id,
            operator_id=operator_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            detail=detail,
        )
        db.add(db_obj)
        return db_obj
