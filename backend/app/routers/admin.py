from typing import List
from uuid import UUID
from datetime import datetime, date, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.deps.db import get_db
from app.deps.services import (
    get_user_service,
    get_board_service,
    get_board_master_service,
    get_announcement_service,
)
from app.deps.auth import require_admin
from app.models.user import User
from app.models.post import Post
from app.models.comment import Comment
from app.models.board import Board

from app.schemas.response import (
    ApiResponse,
    PaginatedResponse,
    PaginatedData,
    PaginationInfo,
)
from app.schemas.user import AdminUserData, UpdateUserStatusRequest, MuteUserRequest
from app.schemas.admin import AdminStatsResponse
from app.schemas.board import BoardCreate, BoardUpdate, BoardRead
from app.schemas.board_master import BoardMasterRead, AddBoardMasterRequest
from app.schemas.announcement import (
    AnnouncementCreate,
    AnnouncementUpdate,
    AnnouncementRead,
)
from app.services.user_service import UserService
from app.services.board_service import BoardService
from app.services.board_master_service import BoardMasterService
from app.services.announcement_service import AnnouncementService

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
    dependencies=[Depends(require_admin)],
)


@router.get("/stats", response_model=ApiResponse[AdminStatsResponse])
def get_system_stats(db: Session = Depends(get_db)):
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
def admin_list_users(
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
def admin_update_user_status(
    id: str,
    payload: UpdateUserStatusRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
    service: UserService = Depends(get_user_service),
):
    # 管理员不能 ban 自己
    if str(id) == str(current_user.id) and payload.status == "banned":
        raise HTTPException(status_code=400, detail="Cannot ban yourself")
    return ApiResponse(data=service.update_status(db, id, payload))


@router.get("/boards", response_model=ApiResponse[List[BoardRead]])
def admin_list_boards(
    db: Session = Depends(get_db), service: BoardService = Depends(get_board_service)
):
    return ApiResponse(data=service.get_all(db))


@router.post(
    "/boards",
    response_model=ApiResponse[BoardRead],
    status_code=status.HTTP_201_CREATED,
)
def admin_create_board(
    payload: BoardCreate,
    db: Session = Depends(get_db),
    service: BoardService = Depends(get_board_service),
):
    if service.get_by_slug(db, payload.slug):
        raise HTTPException(status_code=400, detail="Board slug exists")
    return ApiResponse(data=service.create(db, obj_in=payload))


@router.patch("/boards/{id}", response_model=ApiResponse[BoardRead])
def admin_edit_board(
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
def admin_delete_board(
    id: UUID,
    db: Session = Depends(get_db),
    service: BoardService = Depends(get_board_service),
):
    board = service.get_by_id(db, id)
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")
    service.remove(db, db_obj=board)


# ── Board Master Management ──


@router.get(
    "/boards/{board_id}/masters",
    response_model=ApiResponse[List[BoardMasterRead]],
)
def admin_list_board_masters(
    board_id: UUID,
    db: Session = Depends(get_db),
    service: BoardMasterService = Depends(get_board_master_service),
):
    """列出板块的版主（仅管理员）"""
    board = (
        db.query(Board).filter(Board.id == board_id, Board.deleted_at.is_(None)).first()
    )
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")
    return ApiResponse(data=service.list_for_board(db, board_id))


@router.post(
    "/boards/{board_id}/masters",
    response_model=ApiResponse[BoardMasterRead],
    status_code=status.HTTP_201_CREATED,
)
def admin_add_board_master(
    board_id: UUID,
    payload: AddBoardMasterRequest,
    db: Session = Depends(get_db),
    service: BoardMasterService = Depends(get_board_master_service),
):
    """添加版主（仅管理员）"""
    board = (
        db.query(Board).filter(Board.id == board_id, Board.deleted_at.is_(None)).first()
    )
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")
    user = (
        db.query(User)
        .filter(User.id == payload.user_id, User.deleted_at.is_(None))
        .first()
    )
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    result = service.add(db, board_id=board_id, user_id=payload.user_id)
    db.refresh(result, attribute_names=["user"])
    return ApiResponse(data=result)


@router.delete(
    "/boards/{board_id}/masters/{user_id}",
    response_model=ApiResponse,
)
def admin_remove_board_master(
    board_id: UUID,
    user_id: UUID,
    db: Session = Depends(get_db),
    service: BoardMasterService = Depends(get_board_master_service),
):
    """移除版主（仅管理员）"""
    service.remove(db, board_id=board_id, user_id=user_id)
    return ApiResponse(message="Board master removed")


# ── Mute / Unmute ──


@router.post("/users/{id}/mute", response_model=ApiResponse[AdminUserData])
def admin_mute_user(
    id: str,
    payload: MuteUserRequest,
    db: Session = Depends(get_db),
    service: UserService = Depends(get_user_service),
):
    """禁言用户（仅管理员）"""
    try:
        uid = UUID(id)
    except ValueError:
        raise HTTPException(status_code=404, detail="User not found")
    user = db.query(User).filter(User.id == uid, User.deleted_at.is_(None)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.muted_until = datetime.now(timezone.utc) + timedelta(
        minutes=payload.duration_minutes
    )
    db.commit()
    db.refresh(user)
    return ApiResponse(data=service.get_admin_user_data(user))


@router.delete("/users/{id}/mute", response_model=ApiResponse)
def admin_unmute_user(
    id: str,
    db: Session = Depends(get_db),
):
    """解除禁言（仅管理员）"""
    try:
        uid = UUID(id)
    except ValueError:
        raise HTTPException(status_code=404, detail="User not found")
    user = db.query(User).filter(User.id == uid, User.deleted_at.is_(None)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.muted_until = None
    db.commit()
    return ApiResponse(message="User unmuted")


# ---------- announcements ----------


@router.get("/announcements", response_model=ApiResponse[list[AnnouncementRead]])
def admin_list_announcements(
    db: Session = Depends(get_db),
    service: AnnouncementService = Depends(get_announcement_service),
):
    """管理端列表（包含未发布/已过期，按创建时间倒序）。"""
    return ApiResponse(data=service.list_all(db))


@router.post(
    "/announcements",
    response_model=ApiResponse[AnnouncementRead],
    status_code=status.HTTP_201_CREATED,
)
def admin_create_announcement(
    payload: AnnouncementCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
    service: AnnouncementService = Depends(get_announcement_service),
):
    return ApiResponse(
        data=service.create(db, obj_in=payload, admin_id=current_user.id)
    )


@router.patch("/announcements/{id}", response_model=ApiResponse[AnnouncementRead])
def admin_edit_announcement(
    id: UUID,
    payload: AnnouncementUpdate,
    db: Session = Depends(get_db),
    service: AnnouncementService = Depends(get_announcement_service),
):
    announcement = service.get_by_id(db, id)
    if not announcement:
        raise HTTPException(status_code=404, detail="Announcement not found")
    return ApiResponse(data=service.update(db, db_obj=announcement, obj_in=payload))


@router.delete("/announcements/{id}", status_code=status.HTTP_204_NO_CONTENT)
def admin_delete_announcement(
    id: UUID,
    db: Session = Depends(get_db),
    service: AnnouncementService = Depends(get_announcement_service),
):
    announcement = service.get_by_id(db, id)
    if not announcement:
        raise HTTPException(status_code=404, detail="Announcement not found")
    service.remove(db, db_obj=announcement)
