from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Query
from fastapi import status
from sqlalchemy.orm import Session

from app.deps import get_current_user
from app.deps import get_db
from app.deps import require_admin
from app.deps.services import get_report_service
from app.models.report import ReportStatus
from app.models.user import User
from app.schemas.report import ReportCreate
from app.schemas.report import ReportRead
from app.schemas.report import ReportResolveRequest
from app.schemas.response import ApiResponse
from app.schemas.response import PaginatedData
from app.schemas.response import PaginatedResponse
from app.schemas.response import PaginationInfo
from app.services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.post(
    "/",
    response_model=ApiResponse[ReportRead],
    status_code=status.HTTP_201_CREATED,
)
def create_report(
    payload: ReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: ReportService = Depends(get_report_service),
):
    report = service.create(db, obj_in=payload, reporter_id=current_user.id)
    return ApiResponse(data=report)


@router.get("/", response_model=PaginatedResponse[ReportRead])
def list_reports(
    report_status: ReportStatus | None = Query(default=None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
    service: ReportService = Depends(get_report_service),
):
    items, total = service.list_reports(
        db, status=report_status, page=page, page_size=page_size
    )
    total_pages = (total + page_size - 1) // page_size
    return PaginatedResponse(
        data=PaginatedData(
            items=items,
            pagination=PaginationInfo(
                page=page,
                page_size=page_size,
                total=total,
                total_pages=total_pages,
            ),
        )
    )


@router.patch("/{report_id}/resolve", response_model=ApiResponse[ReportRead])
def handle_report(
    report_id: UUID,
    payload: ReportResolveRequest,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),
    service: ReportService = Depends(get_report_service),
):
    if payload.status == ReportStatus.RESOLVED:
        report = service.resolve(
            db,
            report_id=report_id,
            operator_id=current_admin.id,
            result_note=payload.result_note,
        )
    elif payload.status == ReportStatus.DISMISSED:
        report = service.dismiss(
            db,
            report_id=report_id,
            operator_id=current_admin.id,
            result_note=payload.result_note,
        )
    else:
        raise HTTPException(
            status_code=422,
            detail="Report status must be resolved or dismissed",
        )

    return ApiResponse(data=report)
