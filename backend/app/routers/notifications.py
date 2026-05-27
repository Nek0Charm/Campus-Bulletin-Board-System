from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Query
from sqlalchemy.orm import Session

from app.deps import get_current_user
from app.deps import get_db
from app.deps import get_notification_service
from app.models import User
from app.schemas.notification import NotificationMarkAllReadResult
from app.schemas.notification import NotificationRead
from app.schemas.notification import NotificationUnreadCount
from app.schemas.response import ApiResponse
from app.schemas.response import PaginatedData
from app.schemas.response import PaginatedResponse
from app.schemas.response import PaginationInfo
from app.services import NotificationService

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=PaginatedResponse[NotificationRead])
@router.get(
    "/", response_model=PaginatedResponse[NotificationRead], include_in_schema=False
)
def list_notifications(
    page: int = Query(ge=1, default=1),
    page_size: int = Query(ge=1, le=100, default=20),
    unread_only: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
):
    items, total = service.list_for_user(
        db,
        user_id=current_user.id,
        page=page,
        page_size=page_size,
        unread_only=unread_only,
    )
    return PaginatedResponse[NotificationRead](
        data=PaginatedData[NotificationRead](
            items=items,
            pagination=PaginationInfo(
                page=page,
                page_size=page_size,
                total=total,
                total_pages=(total + page_size - 1) // page_size,
            ),
        )
    )


@router.get("/unread-count", response_model=ApiResponse[NotificationUnreadCount])
def get_unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
):
    return ApiResponse[NotificationUnreadCount](
        data=NotificationUnreadCount(
            unread_count=service.get_unread_count(db, user_id=current_user.id)
        )
    )


@router.put("/{notification_id}/read", response_model=ApiResponse[NotificationRead])
def mark_as_read(
    notification_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
):
    notification = service.get_for_user(
        db, notification_id=notification_id, user_id=current_user.id
    )
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    return ApiResponse[NotificationRead](
        data=service.mark_read(db, db_obj=notification)
    )


@router.put("/read-all", response_model=ApiResponse[NotificationMarkAllReadResult])
def mark_all_as_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
):
    updated_count = service.mark_all_read(db, user_id=current_user.id)
    unread_count = service.get_unread_count(db, user_id=current_user.id)
    return ApiResponse[NotificationMarkAllReadResult](
        data=NotificationMarkAllReadResult(
            updated_count=updated_count,
            unread_count=unread_count,
        )
    )
