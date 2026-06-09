from datetime import datetime
from datetime import timezone
from typing import List
from typing import Tuple
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.comment import Comment
from app.models.comment import CommentStatus
from app.models.moderation_log import ModerationAction
from app.models.post import Post
from app.models.post import PostStatus
from app.models.report import Report
from app.models.report import ReportStatus
from app.models.report import ReportTargetType
from app.schemas.report import ReportCreate
from app.services.moderation_service import ModerationService


class ReportService:
    def create(self, db: Session, *, obj_in: ReportCreate, reporter_id: UUID) -> Report:
        self._ensure_target_exists(db, obj_in.target_type.value, obj_in.target_id)

        db_obj = Report(
            reporter_id=reporter_id,
            target_type=obj_in.target_type.value,
            target_id=obj_in.target_id,
            reason=obj_in.reason,
            status=ReportStatus.PENDING.value,
        )
        db.add(db_obj)
        try:
            db.commit()
        except Exception:
            db.rollback()
            raise
        db.refresh(db_obj)
        return db_obj

    def list_reports(
        self,
        db: Session,
        *,
        status: ReportStatus | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Report], int]:
        query = db.query(Report).filter(Report.deleted_at.is_(None))
        if status is not None:
            query = query.filter(Report.status == status.value)

        query = query.order_by(desc(Report.created_at))
        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()
        return items, total

    def resolve(
        self,
        db: Session,
        *,
        report_id: UUID,
        operator_id: UUID,
        result_note: str | None = None,
    ) -> Report:
        report = self._get_pending_report(db, report_id)
        self._hide_target(db, report.target_type, report.target_id)
        return self._handle_report(
            db,
            report=report,
            operator_id=operator_id,
            status=ReportStatus.RESOLVED,
            action=ModerationAction.RESOLVE_REPORT,
            result_note=result_note,
        )

    def dismiss(
        self,
        db: Session,
        *,
        report_id: UUID,
        operator_id: UUID,
        result_note: str | None = None,
    ) -> Report:
        report = self._get_pending_report(db, report_id)
        return self._handle_report(
            db,
            report=report,
            operator_id=operator_id,
            status=ReportStatus.DISMISSED,
            action=ModerationAction.DISMISS_REPORT,
            result_note=result_note,
        )

    def _get_pending_report(self, db: Session, report_id: UUID) -> Report:
        report = (
            db.query(Report)
            .filter(Report.id == report_id, Report.deleted_at.is_(None))
            .first()
        )
        if report is None:
            raise HTTPException(status_code=404, detail="Report not found")
        if report.status != ReportStatus.PENDING.value:
            raise HTTPException(
                status_code=409, detail="Report has already been handled"
            )
        return report

    def _handle_report(
        self,
        db: Session,
        *,
        report: Report,
        operator_id: UUID,
        status: ReportStatus,
        action: ModerationAction,
        result_note: str | None,
    ) -> Report:
        now = datetime.now(timezone.utc)
        report.status = status.value
        report.handled_by = operator_id
        report.handled_at = now
        report.result_note = result_note
        report.updated_at = now

        ModerationService().create_log(
            db,
            report_id=report.id,
            operator_id=operator_id,
            action=action.value,
            target_type=report.target_type,
            target_id=report.target_id,
            detail=result_note,
        )
        try:
            db.commit()
        except Exception:
            db.rollback()
            raise
        db.refresh(report)
        return report

    def _ensure_target_exists(
        self, db: Session, target_type: str, target_id: UUID
    ) -> None:
        target = self._get_target(db, target_type, target_id)
        if target is None:
            raise HTTPException(status_code=404, detail="Report target not found")

    def _hide_target(self, db: Session, target_type: str, target_id: UUID) -> None:
        target = self._get_target(db, target_type, target_id)
        if target is None:
            raise HTTPException(status_code=404, detail="Report target not found")

        if target_type == ReportTargetType.POST.value:
            target.status = PostStatus.HIDDEN.value
        elif target_type == ReportTargetType.COMMENT.value:
            target.status = CommentStatus.HIDDEN.value

    def _get_target(self, db: Session, target_type: str, target_id: UUID):
        if target_type == ReportTargetType.POST.value:
            return (
                db.query(Post)
                .filter(Post.id == target_id, Post.deleted_at.is_(None))
                .first()
            )
        if target_type == ReportTargetType.COMMENT.value:
            return (
                db.query(Comment)
                .filter(Comment.id == target_id, Comment.deleted_at.is_(None))
                .first()
            )
        raise HTTPException(status_code=422, detail="Unsupported report target type")
