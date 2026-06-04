from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.comment import Comment
from app.models.like import CommentLike, PostLike
from app.models.post import Post


class LikeService:
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
