"""
Concurrency / race-condition tests for Likes (post likes + comment likes).

Covers lost-update races on like_count and duplicate-detection via DB constraints.
Uses ThreadPoolExecutor + monkeypatch delays to widen race windows.
"""

import time
from unittest.mock import Mock
from uuid import UUID

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import get_db
from app.deps import get_email_service
from app.main import app
from app.models.base import Base
from app.models.board import Board
from app.models.comment import Comment
from app.models.like import CommentLike, PostLike
from app.models.post import Post
from app.services.email_service import EmailService
from app.services.like_service import LikeService
from tests.concurrency_utils import race_requests

SQLALCHEMY_DATABASE_URL = "sqlite:///test_likes_concurrency.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def _setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def _override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def _make_mock_email_service() -> EmailService:
    import app.services.email_service as mod

    svc = EmailService()
    svc.send_verification_email = Mock()
    svc.generate_verify_token = mod.EmailService.generate_verify_token.__get__(
        svc, EmailService
    )
    svc.decode_verify_token = mod.EmailService.decode_verify_token.__get__(
        svc, EmailService
    )
    return svc


def _override_get_email_service():
    return _make_mock_email_service()


@pytest.fixture()
def client():
    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_email_service] = _override_get_email_service
    c = TestClient(app)
    yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


AUTH_PREFIX = "/api/v1/auth"
LIKES_PREFIX = "/api/v1/likes"


def _register_and_login(
    client, db_session, username="likeuser", email="like@example.com"
) -> tuple[str, str]:
    client.post(
        f"{AUTH_PREFIX}/register",
        json={"username": username, "email": email, "password": "securepass123"},
    )
    from app.models.user import User

    user = db_session.query(User).filter(User.username == username).first()
    user.email_verified = True
    db_session.commit()

    resp = client.post(
        f"{AUTH_PREFIX}/login",
        json={"account": username, "password": "securepass123"},
    )
    data = resp.json()["data"]
    return data["access_token"], data["user"]["id"]


def _create_board(db_session) -> Board:
    board = Board(name="Test Board", slug="test-board", sort_order=0)
    db_session.add(board)
    db_session.commit()
    db_session.refresh(board)
    return board


def _create_post(db_session, author_id: str, board_id) -> Post:
    from datetime import datetime, timezone

    post = Post(
        title="Test Post",
        content="Hello world",
        author_id=UUID(author_id),
        board_id=board_id,
        published_at=datetime.now(timezone.utc),
    )
    db_session.add(post)
    db_session.commit()
    db_session.refresh(post)
    return post


def _create_comment(db_session, author_id: str, post_id) -> Comment:
    comment = Comment(
        post_id=post_id,
        author_id=UUID(author_id),
        content="Test comment",
    )
    db_session.add(comment)
    db_session.commit()
    db_session.refresh(comment)
    return comment


# ── Like count lost-update tests ──────────────────────────────────


class TestLikeCountConcurrency:
    def test_two_users_like_same_post_lost_update(
        self, client, db_session, monkeypatch
    ):
        """2 users concurrently like same post: like_count stays at 1 instead of 2."""
        token_a, uid_a = _register_and_login(
            client, db_session, "like_user_a", "a@test.com"
        )
        token_b, uid_b = _register_and_login(
            client, db_session, "like_user_b", "b@test.com"
        )
        board = _create_board(db_session)
        post = _create_post(db_session, uid_a, board.id)

        # Inject delay after the existence check to widen the race window
        def delayed_like_post(self, db, *, post_id, user_id):
            post_obj = (
                db.query(Post)
                .filter(Post.id == post_id, Post.deleted_at.is_(None))
                .first()
            )
            if not post_obj:
                raise HTTPException(status_code=404, detail="Post not found")
            existing = (
                db.query(PostLike)
                .filter(PostLike.post_id == post_id, PostLike.user_id == user_id)
                .first()
            )
            if existing:
                raise HTTPException(status_code=409, detail="Already liked")
            time.sleep(0.05)
            db.add(PostLike(post_id=post_id, user_id=user_id))
            post_obj.like_count += 1
            try:
                db.commit()
            except Exception:
                db.rollback()
                raise
            db.refresh(post_obj)
            return post_obj

        monkeypatch.setattr(LikeService, "like_post", delayed_like_post)

        def make_like(token):
            c = TestClient(app)
            return c.post(
                f"{LIKES_PREFIX}/posts/{post.id}",
                headers={"Authorization": f"Bearer {token}"},
            )

        db_session.refresh(post)
        actual_likes = (
            db_session.query(PostLike).filter(PostLike.post_id == post.id).count()
        )

        assert actual_likes == 2, f"Expected 2 PostLike rows, got {actual_likes}"
        assert (
            post.like_count == 1
        ), f"BUG: like_count should be 2, got {post.like_count} (lost update)"
        assert post.like_count != actual_likes

    def test_same_user_duplicate_like_prevented(self, client, db_session, monkeypatch):
        """Same user sends 2 concurrent likes: one succeeds, one fails."""
        token, uid = _register_and_login(client, db_session)
        board = _create_board(db_session)
        post = _create_post(db_session, uid, board.id)

        def delayed_like_post(self, db, *, post_id, user_id):
            post_obj = (
                db.query(Post)
                .filter(Post.id == post_id, Post.deleted_at.is_(None))
                .first()
            )
            if not post_obj:
                raise HTTPException(status_code=404, detail="Post not found")
            existing = (
                db.query(PostLike)
                .filter(PostLike.post_id == post_id, PostLike.user_id == user_id)
                .first()
            )
            if existing:
                raise HTTPException(status_code=409, detail="Already liked")
            time.sleep(0.05)
            from sqlalchemy.exc import IntegrityError

            db.add(PostLike(post_id=post_id, user_id=user_id))
            post_obj.like_count += 1
            try:
                db.commit()
            except IntegrityError:
                db.rollback()
                raise HTTPException(status_code=409, detail="Already liked")
            except Exception:
                db.rollback()
                raise
            db.refresh(post_obj)
            return post_obj

        monkeypatch.setattr(LikeService, "like_post", delayed_like_post)

        def make_like():
            c = TestClient(app)
            return c.post(
                f"{LIKES_PREFIX}/posts/{post.id}",
                headers={"Authorization": f"Bearer {token}"},
            )

        responses = race_requests([make_like, make_like])

        # After the IntegrityError fix, duplicate should return 409.
        statuses = [r.status_code for r in responses]
        assert 200 in statuses, f"Expected at least one 200, got {statuses}"
        assert 409 in statuses, f"Expected one 409, got {statuses}"

        db_session.refresh(post)
        actual_likes = (
            db_session.query(PostLike).filter(PostLike.post_id == post.id).count()
        )
        assert actual_likes == 1, f"Expected 1 PostLike row, got {actual_likes}"
        assert post.like_count == 1

    def test_two_users_like_same_comment_lost_update(
        self, client, db_session, monkeypatch
    ):
        """2 users concurrently like same comment: like_count lost update."""
        token_a, uid_a = _register_and_login(
            client, db_session, "like_user_c", "c@test.com"
        )
        token_b, uid_b = _register_and_login(
            client, db_session, "like_user_d", "d@test.com"
        )
        board = _create_board(db_session)
        post = _create_post(db_session, uid_a, board.id)
        comment = _create_comment(db_session, uid_a, post.id)

        def delayed_like_comment(self, db, *, comment_id, user_id):
            comment_obj = (
                db.query(Comment)
                .filter(Comment.id == comment_id, Comment.deleted_at.is_(None))
                .first()
            )
            if not comment_obj:
                raise HTTPException(status_code=404, detail="Comment not found")
            existing = (
                db.query(CommentLike)
                .filter(
                    CommentLike.comment_id == comment_id,
                    CommentLike.user_id == user_id,
                )
                .first()
            )
            if existing:
                raise HTTPException(status_code=409, detail="Already liked")
            time.sleep(0.05)
            db.add(CommentLike(comment_id=comment_id, user_id=user_id))
            comment_obj.like_count += 1
            try:
                db.commit()
            except Exception:
                db.rollback()
                raise
            db.refresh(comment_obj)
            return comment_obj

        monkeypatch.setattr(LikeService, "like_comment", delayed_like_comment)

        def make_like(token):
            c = TestClient(app)
            return c.post(
                f"{LIKES_PREFIX}/comments/{comment.id}",
                headers={"Authorization": f"Bearer {token}"},
            )

        db_session.refresh(comment)
        actual_likes = (
            db_session.query(CommentLike)
            .filter(CommentLike.comment_id == comment.id)
            .count()
        )

        assert actual_likes == 2, f"Expected 2 CommentLike rows, got {actual_likes}"
        assert (
            comment.like_count == 1
        ), f"BUG: like_count should be 2, got {comment.like_count} (lost update)"
        assert comment.like_count != actual_likes

    def test_two_users_unlike_lost_update(self, client, db_session, monkeypatch):
        """2 users both like then both unlike concurrently: count stays at 1 instead of 0."""
        token_a, uid_a = _register_and_login(
            client, db_session, "unlike_a", "ua@test.com"
        )
        token_b, uid_b = _register_and_login(
            client, db_session, "unlike_b", "ub@test.com"
        )
        board = _create_board(db_session)
        post = _create_post(db_session, uid_a, board.id)

        # Both users like the post sequentially first
        client.post(
            f"{LIKES_PREFIX}/posts/{post.id}",
            headers={"Authorization": f"Bearer {token_a}"},
        )
        client.post(
            f"{LIKES_PREFIX}/posts/{post.id}",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        db_session.refresh(post)
        assert post.like_count == 2

        # Inject delay in unlike_post after the existence check
        def delayed_unlike_post(self, db, *, post_id, user_id):
            post_obj = (
                db.query(Post)
                .filter(Post.id == post_id, Post.deleted_at.is_(None))
                .first()
            )
            if not post_obj:
                raise HTTPException(status_code=404, detail="Post not found")
            existing = (
                db.query(PostLike)
                .filter(PostLike.post_id == post_id, PostLike.user_id == user_id)
                .first()
            )
            if not existing:
                raise HTTPException(status_code=404, detail="Like not found")
            time.sleep(0.05)
            db.delete(existing)
            post_obj.like_count = max(0, post_obj.like_count - 1)
            try:
                db.commit()
            except Exception:
                db.rollback()
                raise
            db.refresh(post_obj)
            return post_obj

        monkeypatch.setattr(LikeService, "unlike_post", delayed_unlike_post)

        def make_unlike(token):
            c = TestClient(app)
            return c.delete(
                f"{LIKES_PREFIX}/posts/{post.id}",
                headers={"Authorization": f"Bearer {token}"},
            )

        race_requests([lambda: make_unlike(token_a), lambda: make_unlike(token_b)])

        db_session.refresh(post)
        actual_likes = (
            db_session.query(PostLike).filter(PostLike.post_id == post.id).count()
        )

        # Both unlikes delete their own PostLike rows, so 0 rows should remain
        assert actual_likes == 0, f"Expected 0 PostLike rows, got {actual_likes}"
        # BUG: both read like_count=2, both write max(0, 1) = 1
        assert (
            post.like_count == 1
        ), f"BUG: like_count should be 0, got {post.like_count} (lost update on unlike)"

    def test_three_users_like_same_post_lost_update(
        self, client, db_session, monkeypatch
    ):
        """3-way race: count could be 1 or 2 instead of 3."""
        tokens = []
        for i in range(3):
            token, uid = _register_and_login(
                client, db_session, f"racer_{i}", f"racer_{i}@test.com"
            )
            tokens.append(token)

        board = _create_board(db_session)
        # Use first user's uid for post author
        resp = client.post(
            f"{AUTH_PREFIX}/login",
            json={"account": "racer_0", "password": "securepass123"},
        )
        uid0 = resp.json()["data"]["user"]["id"]
        post = _create_post(db_session, uid0, board.id)

        def delayed_like_post(self, db, *, post_id, user_id):
            post_obj = (
                db.query(Post)
                .filter(Post.id == post_id, Post.deleted_at.is_(None))
                .first()
            )
            if not post_obj:
                raise HTTPException(status_code=404, detail="Post not found")
            existing = (
                db.query(PostLike)
                .filter(PostLike.post_id == post_id, PostLike.user_id == user_id)
                .first()
            )
            if existing:
                raise HTTPException(status_code=409, detail="Already liked")
            time.sleep(0.08)
            db.add(PostLike(post_id=post_id, user_id=user_id))
            post_obj.like_count += 1
            try:
                db.commit()
            except Exception:
                db.rollback()
                raise
            db.refresh(post_obj)
            return post_obj

        monkeypatch.setattr(LikeService, "like_post", delayed_like_post)

        def make_like(token):
            c = TestClient(app)
            return c.post(
                f"{LIKES_PREFIX}/posts/{post.id}",
                headers={"Authorization": f"Bearer {token}"},
            )

        race_requests([lambda t=t: make_like(t) for t in tokens])

        db_session.refresh(post)
        actual_likes = (
            db_session.query(PostLike).filter(PostLike.post_id == post.id).count()
        )

        assert actual_likes == 3, f"Expected 3 PostLike rows, got {actual_likes}"
        assert (
            post.like_count < 3
        ), f"BUG: like_count should be 3, got {post.like_count} (lost update in 3-way race)"
