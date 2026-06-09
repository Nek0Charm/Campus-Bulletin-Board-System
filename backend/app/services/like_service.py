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
        actor = db.query(User).filter(User.id == user_id).first()
        if actor:
            self._notify_like_post(db, post=post, actor=actor)
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
        actor = db.query(User).filter(User.id == user_id).first()
        if actor:
            self._notify_like_comment(db, comment=comment, actor=actor)
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

    def get_liked_comment_ids_for_post(
        self, db: Session, *, post_id: UUID, user_id: UUID
    ) -> list[UUID]:
        """Return comment IDs the user has liked within a given post."""
        rows = (
            db.query(CommentLike.comment_id)
            .join(Comment, Comment.id == CommentLike.comment_id)
            .filter(
                Comment.post_id == post_id,
                CommentLike.user_id == user_id,
                Comment.deleted_at.is_(None),
            )
            .all()
        )
        return [row[0] for row in rows]

    def is_post_liked(self, db: Session, *, post_id: UUID, user_id: UUID) -> bool:
        """Check if a user has liked a post."""
        return (
            db.query(PostLike)
            .filter(PostLike.post_id == post_id, PostLike.user_id == user_id)
            .first()
            is not None
        )

    # ------------------------------------------------------------------
    # private helpers
    # ------------------------------------------------------------------

    def _notify_like_post(self, db: Session, *, post: Post, actor: User) -> None:
        if self._notification_service is None:
            return
        if actor.id == post.author_id:
            return
        # 去重：如果已有同一人对同一帖子的点赞通知，不再重复创建
        existing = self._notification_service.find_similar(
            db,
            recipient_id=post.author_id,
            actor_id=actor.id,
            type="like",
            related_type="post",
            related_id=post.id,
        )
        if existing:
            return
        try:
            self._notification_service.create(
                db,
                recipient_id=post.author_id,
                actor_id=actor.id,
                type="like",
                title="新点赞",
                content=f"{actor.nickname} 赞了你的帖子《{post.title}》",
                related_type="post",
                related_id=post.id,
            )
        except Exception:
            pass

    def _notify_like_comment(
        self, db: Session, *, comment: Comment, actor: User
    ) -> None:
        if self._notification_service is None:
            return
        if actor.id == comment.author_id:
            return
        # 去重：如果已有同一人对同一评论的点赞通知，不再重复创建
        existing = self._notification_service.find_similar(
            db,
            recipient_id=comment.author_id,
            actor_id=actor.id,
            type="like",
            related_type="comment",
            related_id=comment.id,
        )
        if existing:
            return
        try:
            self._notification_service.create(
                db,
                recipient_id=comment.author_id,
                actor_id=actor.id,
                type="like",
                title="新点赞",
                content=f"{actor.nickname} 赞了你的评论",
                related_type="comment",
                related_id=comment.id,
            )
        except Exception:
            pass
