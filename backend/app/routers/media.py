from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import UploadFile
from fastapi import status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.deps.auth import get_current_user
from app.deps.db import get_db
from app.deps.services import get_media_service
from app.models.user import User
from app.schemas.media import MediaUploadResponse
from app.schemas.media import MediaRead
from app.schemas.media import PostAttachmentCreate
from app.schemas.media import PostAttachmentRead
from app.schemas.response import ApiResponse
from app.services.media_service import MediaService

router = APIRouter(prefix="/media", tags=["Media"])


@router.post(
    "/upload",
    response_model=ApiResponse[MediaUploadResponse],
    status_code=status.HTTP_201_CREATED,
)
async def upload_media(
    file: UploadFile,
    source_type: str = "post",
    source_id: UUID | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: MediaService = Depends(get_media_service),
):
    if source_type not in ("post", "comment", "avatar"):
        raise HTTPException(status_code=400, detail="Invalid source_type")
    if not file.content_type:
        raise HTTPException(status_code=400, detail="Missing content type")

    file_data = await file.read()
    file_size = len(file_data)

    asset = service.upload(
        db,
        file_data=file_data,
        file_name=file.filename or "upload",
        mime_type=file.content_type,
        file_size=file_size,
        uploader_id=current_user.id,
        source_type=source_type,
        source_id=source_id,
    )
    return ApiResponse(
        data=MediaUploadResponse(
            id=asset.id,
            url=asset.url,
            file_name=asset.file_name,
            mime_type=asset.mime_type,
            file_size=asset.file_size,
            width=asset.width,
            height=asset.height,
        )
    )


@router.get("/{id}")
def get_media(
    id: UUID,
    db: Session = Depends(get_db),
    service: MediaService = Depends(get_media_service),
):
    data, mime_type = service.get_file(db, id)
    return Response(content=data, media_type=mime_type)


@router.get("/{id}/info", response_model=ApiResponse[MediaRead])
def get_media_info(
    id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: MediaService = Depends(get_media_service),
):
    asset = service.get_by_id(db, id)
    if not asset:
        raise HTTPException(status_code=404, detail="Media not found")
    return ApiResponse(data=asset)


@router.delete("/{id}", response_model=ApiResponse)
def delete_media(
    id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: MediaService = Depends(get_media_service),
):
    service.delete(
        db, id, user_id=current_user.id, is_admin=(current_user.role == "admin")
    )
    return ApiResponse(message="Media deleted")


@router.post(
    "/posts/{post_id}/attachments",
    response_model=ApiResponse[list[PostAttachmentRead]],
    status_code=status.HTTP_201_CREATED,
)
def attach_to_post(
    post_id: UUID,
    payload: PostAttachmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: MediaService = Depends(get_media_service),
):
    attachments = service.attach_to_post(db, post_id, payload.media_ids)
    return ApiResponse(data=attachments)
