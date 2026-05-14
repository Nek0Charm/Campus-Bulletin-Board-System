from typing import List
from uuid import UUID
from datetime import datetime, date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.deps.db import get_db
from app.deps.services import get_user_service, get_board_service
from app.deps.auth import require_admin
from app.models.user import User
from app.models.post import Post
from app.models.comment import Comment

from app.schemas.response import (
    ApiResponse,
    PaginatedResponse,
    PaginatedData,
    PaginationInfo,
)
from app.schemas.user import AdminUserData, UpdateUserStatusRequest
from app.schemas.admin import AdminStatsResponse
from app.schemas.board import BoardCreate, BoardUpdate, BoardRead
from app.services.user_service import UserService
from app.services.board_service import BoardService

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
    dependencies=[Depends(require_admin)],
)


@router.get("/stats", response_model=ApiResponse[AdminStatsResponse])
async def get_system_stats(db: Session = Depends(get_db)):
    today = date.today()
    stats = {
        "total_users": db.query(func.count(User.id)).scalar(),
        "total_posts": db.query(func.count(Post.id)).scalar(),
        "total_comments": db.query(func.count(Comment.id)).scalar(),
        "new_posts_today": db.query(func.count(Post.id))
        .filter(Post.created_at >= datetime.combine(today, datetime.min.time()))
        .scalar(),
    }
    return ApiResponse(data=stats)


@router.get("/users", response_model=PaginatedResponse[AdminUserData])
async def admin_list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    service: UserService = Depends(get_user_service),
):
    items, total = service.list_users(db, page=page, page_size=page_size)
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


@router.patch("/users/{id}/status", response_model=ApiResponse[AdminUserData])
async def admin_update_user_status(
    id: str,
    payload: UpdateUserStatusRequest,
    db: Session = Depends(get_db),
    service: UserService = Depends(get_user_service),
):
    return ApiResponse(data=service.update_status(db, id, payload))


@router.get("/boards", response_model=ApiResponse[List[BoardRead]])
async def admin_list_boards(
    db: Session = Depends(get_db), service: BoardService = Depends(get_board_service)
):
    return ApiResponse(data=service.get_all(db))


@router.post(
    "/boards",
    response_model=ApiResponse[BoardRead],
    status_code=status.HTTP_201_CREATED,
)
async def admin_create_board(
    payload: BoardCreate,
    db: Session = Depends(get_db),
    service: BoardService = Depends(get_board_service),
):
    if service.get_by_slug(db, payload.slug):
        raise HTTPException(status_code=400, detail="Board slug exists")
    return ApiResponse(data=service.create(db, obj_in=payload))


@router.patch("/boards/{id}", response_model=ApiResponse[BoardRead])
async def admin_edit_board(
    id: UUID,
    payload: BoardUpdate,
    db: Session = Depends(get_db),
    service: BoardService = Depends(get_board_service),
):
    board = service.get_by_id(db, id)
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")
    return ApiResponse(data=service.update(db, db_obj=board, obj_in=payload))


@router.delete("/boards/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_board(
    id: UUID,
    db: Session = Depends(get_db),
    service: BoardService = Depends(get_board_service),
):
    board = service.get_by_id(db, id)
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")
    service.remove(db, db_obj=board)
