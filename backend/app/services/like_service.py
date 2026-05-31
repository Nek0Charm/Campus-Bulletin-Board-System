from typing import Optional
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from typing import TYPE_CHECKING

from app.models.comment import Comment
from app.models.like import CommentLike, PostLike
from app.models.post import Post
from app.models.user import User

if TYPE_CHECKING:
    from app.services.notification_service import NotificationService


class LikeService:
    def __init__(self, notification_service: Optional["NotificationService"] = None):
        self._notification_service = notification_service

    def like_post(self, db: Session, *, post_id: UUID, user_id: UUID) -> Post:
        post = (
            db.query(Post).filter(Post.id == post_id, Post.deleted_at.is_(None)).first()
        )
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")

        existing = (
            db.query(PostLike)
            .filter(PostLike.post_id == post_id, PostLike.user_id == user_id)
            .first()
        )
        if existing:
            raise HTTPException(status_code=409, detail="Already liked")

        db.add(PostLike(post_id=post_id, user_id=user_id))
        post.like_count += 1
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=409, detail="Already liked")
        except Exception:
            db.rollback()
            raise
        db.refresh(post)
        self._notify_like_post(db, post=post, actor_id=user_id)
        return post

    def unlike_post(self, db: Session, *, post_id: UUID, user_id: UUID) -> Post:
        post = (
            db.query(Post).filter(Post.id == post_id, Post.deleted_at.is_(None)).first()
        )
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")

        existing = (
            db.query(PostLike)
            .filter(PostLike.post_id == post_id, PostLike.user_id == user_id)
            .first()
        )
        if not existing:
            raise HTTPException(status_code=404, detail="Like not found")

        db.delete(existing)
        post.like_count = max(0, post.like_count - 1)
        try:
            db.commit()
        except Exception:
            db.rollback()
            raise
        db.refresh(post)
        return post

    def like_comment(self, db: Session, *, comment_id: UUID, user_id: UUID) -> Comment:
        comment = (
            db.query(Comment)
            .filter(Comment.id == comment_id, Comment.deleted_at.is_(None))
            .first()
        )
        if not comment:
            raise HTTPException(status_code=404, detail="Comment not found")

        existing = (
            db.query(CommentLike)
            .filter(
                CommentLike.comment_id == comment_id, CommentLike.user_id == user_id
            )
            .first()
        )
        if existing:
            raise HTTPException(status_code=409, detail="Already liked")

        db.add(CommentLike(comment_id=comment_id, user_id=user_id))
        comment.like_count += 1
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=409, detail="Already liked")
        except Exception:
            db.rollback()
            raise
        db.refresh(comment)
        self._notify_like_comment(db, comment=comment, actor_id=user_id)
        return comment

    def unlike_comment(
        self, db: Session, *, comment_id: UUID, user_id: UUID
    ) -> Comment:
        comment = (
            db.query(Comment)
            .filter(Comment.id == comment_id, Comment.deleted_at.is_(None))
            .first()
        )
        if not comment:
            raise HTTPException(status_code=404, detail="Comment not found")

        existing = (
            db.query(CommentLike)
            .filter(
                CommentLike.comment_id == comment_id, CommentLike.user_id == user_id
            )
            .first()
        )
        if not existing:
            raise HTTPException(status_code=404, detail="Like not found")

        db.delete(existing)
        comment.like_count = max(0, comment.like_count - 1)
        try:
            db.commit()
        except Exception:
            db.rollback()
            raise
        db.refresh(comment)
        return comment

    # ------------------------------------------------------------------
    # private helpers
    # ------------------------------------------------------------------

    def _get_actor_nickname(self, db: Session, user_id: UUID) -> str:
        user = db.query(User).filter(User.id == user_id).first()
        return user.nickname if user else "有人"

    def _notify_like_post(self, db: Session, *, post: Post, actor_id: UUID) -> None:
        if self._notification_service is None:
            return
        if actor_id == post.author_id:
            return
        nickname = self._get_actor_nickname(db, actor_id)
        self._notification_service.create(
            db,
            recipient_id=post.author_id,
            actor_id=actor_id,
            type="like",
            title="新点赞",
            content=f"{nickname} 赞了你的帖子《{post.title}》",
            related_type="post",
            related_id=post.id,
        )

    def _notify_like_comment(
        self, db: Session, *, comment: Comment, actor_id: UUID
    ) -> None:
        if self._notification_service is None:
            return
        if actor_id == comment.author_id:
            return
        nickname = self._get_actor_nickname(db, actor_id)
        self._notification_service.create(
            db,
            recipient_id=comment.author_id,
            actor_id=actor_id,
            type="like",
            title="新点赞",
            content=f"{nickname} 赞了你的评论",
            related_type="comment",
            related_id=comment.id,
        )
