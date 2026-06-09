from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Query
from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.deps import get_current_user
from app.deps import get_db
from app.deps import get_user_service
from app.deps import require_admin
from app.models import User
from app.schemas.media import AvatarUploadResponse
from app.schemas.response import ApiResponse
from app.schemas.response import PaginatedData
from app.schemas.response import PaginatedResponse
from app.schemas.response import PaginationInfo
from app.schemas.user import AdminUserData
from app.schemas.user import UpdateProfileRequest
from app.schemas.user import UpdateUserStatusRequest
from app.schemas.user import UserStats
from app.schemas.user import UserProfileData
from app.schemas.user import UserPublicData
from app.services import UserService
from app.deps.services import get_media_service
from app.services.media_service import MediaService

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=ApiResponse[UserProfileData])
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
):
    return ApiResponse[UserProfileData](data=service.get_profile(current_user))


@router.get("/me/stats", response_model=ApiResponse[UserStats])
def get_current_user_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
):
    return ApiResponse[UserStats](data=service.get_stats(db, current_user.id))


@router.patch("/me", response_model=ApiResponse[UserProfileData])
def update_current_user_profile(
    payload: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    service: UserService = Depends(get_user_service),
):
    return ApiResponse[UserProfileData](
        data=service.update_profile(db, current_user, payload)
    )


@router.get("/{id}", response_model=ApiResponse[UserPublicData])
def get_user_public_profile(
    id: str,
    db: Session = Depends(get_db),
    service: UserService = Depends(get_user_service),
):
    return ApiResponse[UserPublicData](data=service.get_public_profile(db, id))


@router.get("/", response_model=PaginatedResponse[AdminUserData])
def list_users(
    page: int = Query(ge=1, default=1),
    page_size: int = Query(ge=1, le=100, default=20),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
    service: UserService = Depends(get_user_service),
):
    items, total = service.list_users(db, page, page_size)
    total_pages = max(1, -(-total // page_size))
    return PaginatedResponse[AdminUserData](
        data=PaginatedData[AdminUserData](
            items=items,
            pagination=PaginationInfo(
                page=page, page_size=page_size, total=total, total_pages=total_pages
            ),
        )
    )


@router.patch("/{id}/status", response_model=ApiResponse[AdminUserData])
def update_user_status(
    id: str,
    payload: UpdateUserStatusRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
    service: UserService = Depends(get_user_service),
):
    return ApiResponse[AdminUserData](data=service.update_status(db, id, payload))


@router.patch("/me/avatar", response_model=ApiResponse[AvatarUploadResponse])
async def upload_avatar(
    file: UploadFile,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: MediaService = Depends(get_media_service),
):
    if not file.content_type:
        raise HTTPException(status_code=400, detail="Missing content type")

    file_data = await file.read()
    avatar_url = service.update_avatar(
        db,
        file_data=file_data,
        file_name=file.filename or "avatar",
        mime_type=file.content_type,
        file_size=len(file_data),
        user_id=current_user.id,
    )
    return ApiResponse[AvatarUploadResponse](
        data=AvatarUploadResponse(avatar_url=avatar_url)
    )
