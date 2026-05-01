from typing import List, Optional
from uuid import UUID
from datetime import datetime, date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from core.database import get_db
from core.auth import get_current_admin
from models.user import User, UserStatus
from models.post import Post
from models.comment import Comment
from models.board import Board
from schemas.admin import AdminStatsResponse, UserListResponse, BoardCreate, BoardUpdate
from schemas.common import MessageResponse

router = APIRouter(
    prefix="/api/v1/admin",
    tags=["Admin"],
    dependencies=[Depends(get_current_admin)],  # 强制管理员权限校验
)


# --- 系统概况统计 ---
@router.get("/stats", response_model=AdminStatsResponse)
def get_system_stats(db: Session = Depends(get_db)):
    """获取系统概况统计数据（用户、帖子、评论总数及今日新增）"""
    today = date.today()
    return {
        "total_users": db.query(func.count(User.id)).scalar(),
        "total_posts": db.query(func.count(Post.id)).scalar(),
        "total_comments": db.query(func.count(Comment.id)).scalar(),
        "new_posts_today": db.query(func.count(Post.id))
        .filter(Post.created_at >= datetime.combine(today, datetime.min.time()))
        .scalar(),
    }


# --- 用户管理 ---
@router.get("/users", response_model=UserListResponse)
def admin_list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_status: Optional[UserStatus] = None,
    db: Session = Depends(get_db),
):
    """分页获取用户列表，支持按状态筛选"""
    query = db.query(User)
    if user_status:
        query = query.filter(User.status == user_status)

    total = query.count()
    users = query.offset((page - 1) * page_size).limit(page_size).all()

    return {
        "items": users,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": (total + page_size - 1) // page_size,
        },
    }


@router.patch("/users/{user_id}/status", response_model=MessageResponse)
def admin_update_user_status(
    user_id: UUID, new_status: UserStatus, db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 只有当状态真的改变时才更新，减少不必要的 IO
    if user.status != new_status:
        user.status = new_status
        user.updated_at = datetime.now()
        db.commit()

    return {"message": f"User status updated to {new_status}"}


# --- 板块管理 ---
@router.get("/boards", response_model=List[Board])
def admin_list_boards(db: Session = Depends(get_db)):
    """获取所有未被逻辑删除的板块"""
    return (
        db.query(Board)
        .filter(Board.deleted_at.is_(None))
        .order_by(Board.sort_order)
        .all()
    )


@router.post("/boards", response_model=Board, status_code=status.HTTP_201_CREATED)
def admin_create_board(board_in: BoardCreate, db: Session = Depends(get_db)):
    """创建新板块"""
    if db.query(Board).filter(Board.slug == board_in.slug).first():
        raise HTTPException(
            status_code=400, detail="Slug already exists (even in deleted boards)"
        )

    # 使用 model_dump 适配 Pydantic V2
    new_board = Board(**board_in.model_dump())
    db.add(new_board)
    db.commit()
    db.refresh(new_board)
    return new_board


@router.patch("/boards/{board_id}", response_model=Board)
def admin_update_board(
    board_id: UUID, board_in: BoardUpdate, db: Session = Depends(get_db)
):
    """编辑板块内容"""
    board = db.query(Board).filter(Board.id == board_id).first()
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")

    # 统一使用 model_dump
    update_data = board_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(board, field, value)

    board.updated_at = datetime.now()
    db.commit()
    db.refresh(board)
    return board


@router.delete("/boards/{board_id}", status_code=status.HTTP_204_NO_CONTENT)
def admin_delete_board(board_id: UUID, db: Session = Depends(get_db)):
    """逻辑删除板块"""
    board = db.query(Board).filter(Board.id == board_id).first()
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")

    board.deleted_at = datetime.now()
    db.commit()
    return None
