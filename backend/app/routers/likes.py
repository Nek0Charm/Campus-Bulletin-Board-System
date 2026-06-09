from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.deps.auth import get_current_user
from app.deps.db import get_db
from app.deps.services import get_like_service
from app.models.user import User
from app.schemas.like import PostLikeStatus
from app.schemas.response import ApiResponse
from app.services.like_service import LikeService

router = APIRouter(prefix="/likes", tags=["likes"])


@router.get("/my-status", response_model=ApiResponse[PostLikeStatus])
def get_my_like_status(
    post_id: UUID = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: LikeService = Depends(get_like_service),
):
    is_liked = service.is_post_liked(db, post_id=post_id, user_id=current_user.id)
    comment_ids = service.get_liked_comment_ids_for_post(
        db, post_id=post_id, user_id=current_user.id
    )
    return ApiResponse(
        data=PostLikeStatus(
            is_liked=is_liked,
            liked_comment_ids=comment_ids,
        )
    )


@router.post(
    "/posts/{post_id}", response_model=ApiResponse, status_code=status.HTTP_200_OK
)
def like_post(
    post_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: LikeService = Depends(get_like_service),
):
    service.like_post(db, post_id=post_id, user_id=current_user.id)
    return ApiResponse(message="Liked")


@router.delete(
    "/posts/{post_id}", response_model=ApiResponse, status_code=status.HTTP_200_OK
)
def unlike_post(
    post_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: LikeService = Depends(get_like_service),
):
    service.unlike_post(db, post_id=post_id, user_id=current_user.id)
    return ApiResponse(message="Unliked")


@router.post(
    "/comments/{comment_id}", response_model=ApiResponse, status_code=status.HTTP_200_OK
)
def like_comment(
    comment_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: LikeService = Depends(get_like_service),
):
    service.like_comment(db, comment_id=comment_id, user_id=current_user.id)
    return ApiResponse(message="Liked")


@router.delete(
    "/comments/{comment_id}", response_model=ApiResponse, status_code=status.HTTP_200_OK
)
def unlike_comment(
    comment_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: LikeService = Depends(get_like_service),
):
    service.unlike_comment(db, comment_id=comment_id, user_id=current_user.id)
    return ApiResponse(message="Unliked")
