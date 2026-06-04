"""
Concurrency / race-condition tests for Comments.

Covers lost-update races on post.comment_count and comment.reply_count, plus
mixed create/delete races. Uses ThreadPoolExecutor + monkeypatch delays.
"""

import time
from datetime import datetime, timezone
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
from app.models.comment import Comment, CommentStatus
from app.models.post import Post
from app.schemas.comment import CommentCreate
from app.services.comment_service import CommentService
from app.services.email_service import EmailService
from tests.concurrency_utils import race_requests

SQLALCHEMY_DATABASE_URL = "sqlite:///test_comments_concurrency.db"

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


@pytest.fixture()
def client():
    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_email_service] = _make_mock_email_service
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
API_PREFIX = "/api/v1/comments"


def _register_and_login(
    client, db_session, username="commenter", email="c@example.com"
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


def _create_post(db_session, author_id: str) -> Post:
    board = _create_board(db_session)
    post = Post(
        title="Test Post",
        content="Hello",
        author_id=UUID(author_id),
        board_id=board.id,
        published_at=datetime.now(timezone.utc),
    )
    db_session.add(post)
    db_session.commit()
    db_session.refresh(post)
    return post


# ── Comment count lost-update tests ───────────────────────────────


class TestCommentCountConcurrency:
    def test_two_users_comment_lost_update(self, client, db_session, monkeypatch):
        """2 users comment on same post concurrently: comment_count stays at 1 instead of 2."""
        token_a, uid_a = _register_and_login(
            client, db_session, "cmter_a", "ca@test.com"
        )
        token_b, uid_b = _register_and_login(
            client, db_session, "cmter_b", "cb@test.com"
        )
        post = _create_post(db_session, uid_a)

        # Inject delay after post validation, before creating the comment
        def delayed_create(self, db, *, obj_in: CommentCreate, author_id):
            post_obj = (
                db.query(Post)
                .filter(Post.id == obj_in.post_id, Post.deleted_at.is_(None))
                .first()
            )
            if not post_obj:
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
                    raise HTTPException(
                        status_code=404, detail="Parent comment not found"
                    )
                if parent.post_id != obj_in.post_id:
                    raise HTTPException(
                        status_code=400,
                        detail="Parent comment belongs to a different post",
                    )
                parent_comment_id = parent.id
                root_comment_id = parent.root_comment_id or parent.id
                parent.reply_count += 1

            time.sleep(0.05)

            comment = Comment(
                post_id=obj_in.post_id,
                author_id=author_id,
                content=obj_in.content,
                parent_comment_id=parent_comment_id,
                root_comment_id=root_comment_id,
            )
            db.add(comment)
            post_obj.comment_count += 1
            try:
                db.commit()
            except Exception:
                db.rollback()
                raise
            db.refresh(comment)
            db.refresh(comment, attribute_names=["author"])
            return comment

        monkeypatch.setattr(CommentService, "create", delayed_create)

        def make_comment(token):
            c = TestClient(app)
            return c.post(
                f"{API_PREFIX}/",
                json={"post_id": str(post.id), "content": "Concurrent comment"},
                headers={"Authorization": f"Bearer {token}"},
            )

        race_requests([lambda: make_comment(token_a), lambda: make_comment(token_b)])

        db_session.refresh(post)
        actual_comments = (
            db_session.query(Comment)
            .filter(Comment.post_id == post.id, Comment.deleted_at.is_(None))
            .count()
        )

        assert actual_comments == 2, f"Expected 2 comments, got {actual_comments}"
        assert (
            post.comment_count == 1
        ), f"BUG: comment_count should be 2, got {post.comment_count} (lost update)"
        assert post.comment_count != actual_comments

    def test_two_users_delete_comment_lost_update(
        self, client, db_session, monkeypatch
    ):
        """2 users each create a comment then delete concurrently: count stays at 1 instead of 0."""
        token_a, uid_a = _register_and_login(client, db_session, "del_a", "da@test.com")
        token_b, uid_b = _register_and_login(client, db_session, "del_b", "db@test.com")
        post = _create_post(db_session, uid_a)

        # Create one comment per user sequentially
        resp_a = client.post(
            f"{API_PREFIX}/",
            json={"post_id": str(post.id), "content": "Comment A"},
            headers={"Authorization": f"Bearer {token_a}"},
        )
        comment_a_id = resp_a.json()["data"]["id"]

        resp_b = client.post(
            f"{API_PREFIX}/",
            json={"post_id": str(post.id), "content": "Comment B"},
            headers={"Authorization": f"Bearer {token_b}"},
        )
        comment_b_id = resp_b.json()["data"]["id"]

        db_session.refresh(post)
        assert post.comment_count == 2

        # Inject delay in remove() between querying post and writing
        def delayed_remove(self, db, *, db_obj):
            post_obj = (
                db.query(Post)
                .filter(Post.id == db_obj.post_id, Post.deleted_at.is_(None))
                .first()
            )

            time.sleep(0.05)

            db_obj.deleted_at = datetime.now(timezone.utc)
            db_obj.status = CommentStatus.DELETED

            if post_obj:
                post_obj.comment_count = max(0, post_obj.comment_count - 1)

            try:
                db.commit()
            except Exception:
                db.rollback()
                raise

        monkeypatch.setattr(CommentService, "remove", delayed_remove)

        def make_delete(token, comment_id):
            c = TestClient(app)
            return c.delete(
                f"{API_PREFIX}/{comment_id}",
                headers={"Authorization": f"Bearer {token}"},
            )

        race_requests(
            [
                lambda: make_delete(token_a, comment_a_id),
                lambda: make_delete(token_b, comment_b_id),
            ]
        )

        db_session.refresh(post)
        actual_comments = (
            db_session.query(Comment)
            .filter(Comment.post_id == post.id, Comment.deleted_at.is_(None))
            .count()
        )

        assert (
            actual_comments == 0
        ), f"Expected 0 active comments, got {actual_comments}"
        # BUG: both read comment_count=2, both write max(0, 1) = 1
        assert (
            post.comment_count == 1
        ), f"BUG: comment_count should be 0, got {post.comment_count} (lost update on delete)"

    def test_create_and_delete_comment_race(self, client, db_session, monkeypatch):
        """Thread A creates a comment while Thread B deletes a different comment.
        Both read the same count, one increments, one decrements — net count is wrong.
        """
        token_a, uid_a = _register_and_login(
            client, db_session, "race_a", "ra@test.com"
        )
        token_b, uid_b = _register_and_login(
            client, db_session, "race_b", "rb@test.com"
        )
        post = _create_post(db_session, uid_a)

        # Create one comment via user B (to be deleted later)
        resp = client.post(
            f"{API_PREFIX}/",
            json={"post_id": str(post.id), "content": "To be deleted"},
            headers={"Authorization": f"Bearer {token_b}"},
        )
        to_delete_id = resp.json()["data"]["id"]

        db_session.refresh(post)
        assert post.comment_count == 1

        # Delay both create AND remove to make them race
        def delayed_create(self, db, *, obj_in: CommentCreate, author_id):
            post_obj = (
                db.query(Post)
                .filter(Post.id == obj_in.post_id, Post.deleted_at.is_(None))
                .first()
            )
            if not post_obj:
                raise HTTPException(status_code=404, detail="Post not found")
            time.sleep(0.05)
            comment = Comment(
                post_id=obj_in.post_id,
                author_id=author_id,
                content=obj_in.content,
            )
            db.add(comment)
            post_obj.comment_count += 1
            try:
                db.commit()
            except Exception:
                db.rollback()
                raise
            db.refresh(comment)
            db.refresh(comment, attribute_names=["author"])
            return comment

        def delayed_remove(self, db, *, db_obj):
            post_obj = (
                db.query(Post)
                .filter(Post.id == db_obj.post_id, Post.deleted_at.is_(None))
                .first()
            )
            time.sleep(0.05)
            db_obj.deleted_at = datetime.now(timezone.utc)
            db_obj.status = CommentStatus.DELETED
            if post_obj:
                post_obj.comment_count = max(0, post_obj.comment_count - 1)
            try:
                db.commit()
            except Exception:
                db.rollback()
                raise

        # We need both monkeypatches active simultaneously.
        # Monkeypatch create first, then save the modified remove too.
        monkeypatch.setattr(CommentService, "create", delayed_create)
        monkeypatch.setattr(CommentService, "remove", delayed_remove)

        def make_create():
            c = TestClient(app)
            return c.post(
                f"{API_PREFIX}/",
                json={"post_id": str(post.id), "content": "New comment"},
                headers={"Authorization": f"Bearer {token_a}"},
            )

        def make_delete():
            c = TestClient(app)
            return c.delete(
                f"{API_PREFIX}/{to_delete_id}",
                headers={"Authorization": f"Bearer {token_b}"},
            )

        race_requests([make_create, make_delete])

        db_session.refresh(post)
        active_comments = (
            db_session.query(Comment)
            .filter(Comment.post_id == post.id, Comment.deleted_at.is_(None))
            .count()
        )

        # Net effect: one created, one deleted — count should be 1
        assert active_comments == 1, f"Expected 1 active comment, got {active_comments}"
        # BUG: both read 1; create writes 2, delete writes 0 — whichever
        # commits last determines the value, neither is correct (should be 1)
        assert post.comment_count != 1, (
            f"BUG: comment_count should be 1 (net zero change), "
            f"got {post.comment_count} (race between +1 and -1)"
        )

    def test_two_users_reply_lost_update(self, client, db_session, monkeypatch):
        """2 users reply to the same parent comment concurrently: reply_count lost."""
        token_a, uid_a = _register_and_login(
            client, db_session, "reply_a", "rpa@test.com"
        )
        token_b, uid_b = _register_and_login(
            client, db_session, "reply_b", "rpb@test.com"
        )
        post = _create_post(db_session, uid_a)

        # Create root comment
        root_resp = client.post(
            f"{API_PREFIX}/",
            json={"post_id": str(post.id), "content": "Root"},
            headers={"Authorization": f"Bearer {token_a}"},
        )
        root_id = root_resp.json()["data"]["id"]

        # Inject delay in create() after parent validation, before db write
        def delayed_create(self, db, *, obj_in: CommentCreate, author_id):
            post_obj = (
                db.query(Post)
                .filter(Post.id == obj_in.post_id, Post.deleted_at.is_(None))
                .first()
            )
            if not post_obj:
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
                    raise HTTPException(
                        status_code=404, detail="Parent comment not found"
                    )
                if parent.post_id != obj_in.post_id:
                    raise HTTPException(
                        status_code=400,
                        detail="Parent comment belongs to a different post",
                    )
                parent_comment_id = parent.id
                root_comment_id = parent.root_comment_id or parent.id
                parent.reply_count += 1

            time.sleep(0.05)

            comment = Comment(
                post_id=obj_in.post_id,
                author_id=author_id,
                content=obj_in.content,
                parent_comment_id=parent_comment_id,
                root_comment_id=root_comment_id,
            )
            db.add(comment)
            post_obj.comment_count += 1
            try:
                db.commit()
            except Exception:
                db.rollback()
                raise
            db.refresh(comment)
            db.refresh(comment, attribute_names=["author"])
            return comment

        monkeypatch.setattr(CommentService, "create", delayed_create)

        def make_reply(token):
            c = TestClient(app)
            return c.post(
                f"{API_PREFIX}/",
                json={
                    "post_id": str(post.id),
                    "content": "Reply",
                    "parent_comment_id": root_id,
                },
                headers={"Authorization": f"Bearer {token}"},
            )

        race_requests([lambda: make_reply(token_a), lambda: make_reply(token_b)])

        from app.models.comment import Comment as CommentModel

        root = (
            db_session.query(CommentModel)
            .filter(CommentModel.id == UUID(root_id))
            .first()
        )

        # BUG: both replies read reply_count=0, both write 1
        assert (
            root.reply_count == 1
        ), f"BUG: reply_count should be 2, got {root.reply_count} (lost update)"
        actual_replies = (
            db_session.query(CommentModel)
            .filter(
                CommentModel.root_comment_id == UUID(root_id),
                CommentModel.deleted_at.is_(None),
            )
            .count()
        )
        assert actual_replies == 2, f"Expected 2 replies, got {actual_replies}"
        assert root.reply_count != actual_replies
