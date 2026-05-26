from datetime import datetime, timezone
from typing import List, Optional, Tuple
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import desc
from sqlalchemy.orm import Session, joinedload

from app.models.comment import Comment, CommentStatus
from app.models.post import Post
from app.schemas.comment import CommentCreate, CommentUpdate


class CommentService:
    def create(self, db: Session, *, obj_in: CommentCreate, author_id: UUID) -> Comment:
        post = (
            db.query(Post)
            .filter(Post.id == obj_in.post_id, Post.deleted_at.is_(None))
            .first()
        )
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")

        root_comment_id = None
        parent_comment_id = None

        if obj_in.parent_comment_id:
            parent = (
                db.query(Comment)
                .filter(
                    Comment.id == obj_in.parent_comment_id,
                    Comment.deleted_at.is_(None),
                )
                .first()
            )
            if not parent:
                raise HTTPException(status_code=404, detail="Parent comment not found")
            if parent.post_id != obj_in.post_id:
                raise HTTPException(
                    status_code=400, detail="Parent comment belongs to a different post"
                )
            parent_comment_id = parent.id
            # 若父评论是根评论则 root = parent.id，否则 root = parent.root_comment_id
            root_comment_id = parent.root_comment_id or parent.id
            parent.reply_count += 1

        comment = Comment(
            post_id=obj_in.post_id,
            author_id=author_id,
            content=obj_in.content,
            parent_comment_id=parent_comment_id,
            root_comment_id=root_comment_id,
        )
        db.add(comment)
        post.comment_count += 1

        try:
            db.commit()
        except Exception:
            db.rollback()
            raise

        db.refresh(comment)
        # 补全 author 关系
        db.refresh(comment, attribute_names=["author"])
        return comment

    def get_multi(
        self,
        db: Session,
        *,
        post_id: UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Comment], int]:
        """返回根评论列表（楼栋），每条附带其所有回复。"""
        root_q = (
            db.query(Comment)
            .options(joinedload(Comment.author))
            .filter(
                Comment.post_id == post_id,
                Comment.root_comment_id.is_(None),
                Comment.deleted_at.is_(None),
            )
            .order_by(Comment.created_at)
        )
        total = root_q.count()
        roots = root_q.offset((page - 1) * page_size).limit(page_size).all()

        if roots:
            root_ids = [r.id for r in roots]
            replies = (
                db.query(Comment)
                .options(joinedload(Comment.author))
                .filter(
                    Comment.root_comment_id.in_(root_ids),
                    Comment.deleted_at.is_(None),
                )
                .order_by(Comment.created_at)
                .all()
            )
            reply_map: dict[UUID, List[Comment]] = {r.id: [] for r in roots}
            for reply in replies:
                if reply.root_comment_id in reply_map:
                    reply_map[reply.root_comment_id].append(reply)
            for root in roots:
                root._replies = reply_map[root.id]

        return roots, total

    def get_by_id(self, db: Session, comment_id: UUID) -> Optional[Comment]:
        return (
            db.query(Comment)
            .options(joinedload(Comment.author))
            .filter(Comment.id == comment_id, Comment.deleted_at.is_(None))
            .first()
        )

    def update(self, db: Session, *, db_obj: Comment, obj_in: CommentUpdate) -> Comment:
        db_obj.content = obj_in.content
        db_obj.updated_at = datetime.now(timezone.utc)
        try:
            db.commit()
        except Exception:
            db.rollback()
            raise
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, *, db_obj: Comment) -> None:
        post = (
            db.query(Post)
            .filter(Post.id == db_obj.post_id, Post.deleted_at.is_(None))
            .first()
        )

        db_obj.deleted_at = datetime.now(timezone.utc)
        db_obj.status = CommentStatus.DELETED

        if post:
            post.comment_count = max(0, post.comment_count - 1)

        try:
            db.commit()
        except Exception:
            db.rollback()
            raise
