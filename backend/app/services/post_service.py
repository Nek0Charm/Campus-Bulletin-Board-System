from datetime import datetime, timezone
from typing import Optional, Tuple, List
from uuid import UUID
from sqlalchemy import desc
from sqlalchemy.orm import Session, joinedload

from app.models.board import Board
from app.models.post import Post, PostStatus
from app.schemas.post import PostCreate, PostUpdate
from app.utils.search import build_search_document


class PostService:
    def create(self, db: Session, *, obj_in: PostCreate, author_id: UUID) -> Post:
        db_obj = Post(
            **obj_in.model_dump(),
            author_id=author_id,
            search_document=build_search_document(obj_in.title, obj_in.content),
            published_at=datetime.now(timezone.utc),
        )
        db.add(db_obj)
        board = db.query(Board).filter(Board.id == obj_in.board_id).first()
        if board:
            board.post_count = Board.post_count + 1
        try:
            db.commit()
        except Exception:
            db.rollback()
            raise
        db.refresh(db_obj)
        return db_obj

    def get_multi(
        self,
        db: Session,
        *,
        board_id: Optional[UUID] = None,
        author_id: Optional[UUID] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Post], int]:
        query = (
            db.query(Post)
            .options(joinedload(Post.author))
            .filter(Post.deleted_at.is_(None))
        )

        if board_id:
            query = query.filter(Post.board_id == board_id)
        if author_id:
            query = query.filter(Post.author_id == author_id)

        query = query.order_by(desc(Post.is_pinned), desc(Post.created_at))

        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()
        return items, total

    def get_by_id(self, db: Session, id: UUID) -> Optional[Post]:
        return (
            db.query(Post)
            .options(joinedload(Post.author))
            .filter(Post.id == id, Post.deleted_at.is_(None))
            .first()
        )

    def update(self, db: Session, *, db_obj: Post, obj_in: PostUpdate) -> Post:
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)

        if "title" in update_data or "content" in update_data:
            db_obj.search_document = build_search_document(db_obj.title, db_obj.content)

        db_obj.updated_at = datetime.now(timezone.utc)
        try:
            db.commit()
        except Exception:
            db.rollback()
            raise
        db.refresh(db_obj)
        return db_obj

    def update_special_status(
        self, db: Session, *, db_obj: Post, field: str, val: bool
    ) -> Post:
        setattr(db_obj, field, val)
        try:
            db.commit()
        except Exception:
            db.rollback()
            raise
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, *, db_obj: Post) -> Post:
        db_obj.deleted_at = datetime.now(timezone.utc)
        db_obj.status = PostStatus.DELETED
        board = db.query(Board).filter(Board.id == db_obj.board_id).first()
        if board and board.post_count > 0:
            board.post_count = Board.post_count - 1
        try:
            db.commit()
        except Exception:
            db.rollback()
            raise
        return db_obj
