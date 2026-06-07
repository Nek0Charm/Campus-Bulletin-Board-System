from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.deps.db import get_db
from app.deps.services import get_announcement_service
from app.schemas.announcement import AnnouncementRead
from app.schemas.response import ApiResponse
from app.services.announcement_service import AnnouncementService

router = APIRouter(prefix="/announcements", tags=["announcements"])


@router.get("/", response_model=ApiResponse[list[AnnouncementRead]])
def list_announcements(
    db: Session = Depends(get_db),
    service: AnnouncementService = Depends(get_announcement_service),
):
    return ApiResponse(data=service.list_published(db))
