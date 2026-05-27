from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.deps.auth import get_current_user
from app.deps.db import get_db
from app.deps.services import get_comment_service
from app.models.user import User
from app.schemas.comment import (
    CommentCreate,
    CommentRead,
    CommentUpdate,
    CommentWithReplies,
)
from app.schemas.response import (
    ApiResponse,
    PaginatedData,
    PaginatedResponse,
    PaginationInfo,
)
from app.services.comment_service import CommentService

router = APIRouter(prefix="/comments", tags=["comments"])


@router.post(
    "/", response_model=ApiResponse[CommentRead], status_code=status.HTTP_201_CREATED
)
def create_comment(
    payload: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: CommentService = Depends(get_comment_service),
):
    comment = service.create(db, obj_in=payload, author_id=current_user.id)
    return ApiResponse(data=comment)


@router.get("/", response_model=PaginatedResponse[CommentWithReplies])
def list_comments(
    post_id: UUID = Query(...),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    service: CommentService = Depends(get_comment_service),
):
    roots, total = service.get_multi(
        db, post_id=post_id, page=page, page_size=page_size
    )
    items: List[CommentWithReplies] = []
    for root in roots:
        replies = getattr(root, "_replies", [])
        item = CommentWithReplies.model_validate(root)
        item.replies = [CommentRead.model_validate(r) for r in replies]
        items.append(item)
    return PaginatedResponse(
        data=PaginatedData(
            items=items,
            pagination=PaginationInfo(
                page=page,
                page_size=page_size,
                total=total,
                total_pages=(total + page_size - 1) // page_size,
            ),
        )
    )


@router.patch("/{comment_id}", response_model=ApiResponse[CommentRead])
def update_comment(
    comment_id: UUID,
    payload: CommentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: CommentService = Depends(get_comment_service),
):
    comment = service.get_by_id(db, comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    if comment.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Permission denied")
    return ApiResponse(data=service.update(db, db_obj=comment, obj_in=payload))


@router.delete("/{comment_id}", response_model=ApiResponse)
def delete_comment(
    comment_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: CommentService = Depends(get_comment_service),
):
    comment = service.get_by_id(db, comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    if comment.author_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Permission denied")
    service.remove(db, db_obj=comment)
    return ApiResponse(message="Comment deleted")
