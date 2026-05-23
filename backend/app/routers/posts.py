from typing import TYPE_CHECKING, Optional  # 确保导入了 List 和 Optional

if TYPE_CHECKING:
    pass

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.deps.db import get_db
from app.deps.services import get_post_service
from app.deps.auth import get_current_user
from app.models.user import User
from app.schemas.response import (
    ApiResponse,
    PaginatedResponse,
    PaginatedData,
    PaginationInfo,
)
from app.schemas.post import PostCreate, PostUpdate, PostRead
from app.services.post_service import PostService

router = APIRouter(prefix="/posts", tags=["Posts"])


@router.post(
    "/", response_model=ApiResponse[PostRead], status_code=status.HTTP_201_CREATED
)
def create_post(
    payload: PostCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: PostService = Depends(get_post_service),
):
    """发帖：自动填充作者 ID"""
    post = service.create(db, obj_in=payload, author_id=current_user.id)
    return ApiResponse(data=post)


@router.get("/", response_model=PaginatedResponse[PostRead])
def list_posts(
    board_id: Optional[UUID] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    service: PostService = Depends(get_post_service),
):
    """获取帖子列表：支持分页、板块筛选，置顶优先"""
    items, total = service.get_multi(
        db, board_id=board_id, page=page, page_size=page_size
    )
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


@router.get("/{id}", response_model=ApiResponse[PostRead])
def get_post(
    id: UUID,
    db: Session = Depends(get_db),
    service: PostService = Depends(get_post_service),
):
    post = service.get_by_id(db, id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return ApiResponse(data=post)


@router.patch("/{id}", response_model=ApiResponse[PostRead])
def update_post(
    id: UUID,
    payload: PostUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: PostService = Depends(get_post_service),
):
    """编辑帖子：仅限作者或管理员"""
    post = service.get_by_id(db, id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.author_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Permission denied")

    return ApiResponse(data=service.update(db, db_obj=post, obj_in=payload))


@router.delete("/{id}", response_model=ApiResponse)
def delete_post(
    id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: PostService = Depends(get_post_service),
):
    """软删除帖子：仅限作者或管理员"""
    post = service.get_by_id(db, id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.author_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Permission denied")

    service.remove(db, db_obj=post)
    return ApiResponse(message="Post deleted")


@router.patch("/{id}/pin", response_model=ApiResponse[PostRead])
def pin_post(
    id: UUID,
    is_pinned: bool = True,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    service: PostService = Depends(get_post_service),
):
    """置顶/取消置顶：仅管理员"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    post = service.get_by_id(db, id)
    return ApiResponse(
        data=service.update_special_status(
            db, db_obj=post, field="is_pinned", val=is_pinned
        )
    )


@router.patch("/{id}/feature", response_model=ApiResponse[PostRead])
def feature_post(
    id: UUID,
    is_featured: bool = True,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    service: PostService = Depends(get_post_service),
):
    """加精/取消加精：仅管理员"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    post = service.get_by_id(db, id)
    return ApiResponse(
        data=service.update_special_status(
            db, db_obj=post, field="is_featured", val=is_featured
        )
    )
