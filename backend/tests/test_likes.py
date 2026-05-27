"""
Likes 路由集成测试：post likes / comment likes，验证 409、404 和 like_count 同步。
"""

from unittest.mock import Mock
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import get_db
from app.deps import get_email_service
from app.main import app
from app.models.base import Base
from app.models.board import Board
from app.models.comment import Comment
from app.models.post import Post
from app.services.email_service import EmailService

SQLALCHEMY_DATABASE_URL = "sqlite:///test_likes.db"

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


# ── Post likes ──────────────────────────────────────────────


def test_like_post_requires_auth(client, db_session):
    token, user_id = _register_and_login(client, db_session)
    board = _create_board(db_session)
    post = _create_post(db_session, user_id, board.id)

    resp = client.post(f"{LIKES_PREFIX}/posts/{post.id}")
    assert resp.status_code == 401


def test_like_post_success_and_increments_count(client, db_session):
    token, user_id = _register_and_login(client, db_session)
    board = _create_board(db_session)
    post = _create_post(db_session, user_id, board.id)
    assert post.like_count == 0

    resp = client.post(
        f"{LIKES_PREFIX}/posts/{post.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200

    db_session.refresh(post)
    assert post.like_count == 1


def test_like_post_duplicate_returns_409(client, db_session):
    token, user_id = _register_and_login(client, db_session)
    board = _create_board(db_session)
    post = _create_post(db_session, user_id, board.id)

    client.post(
        f"{LIKES_PREFIX}/posts/{post.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    resp = client.post(
        f"{LIKES_PREFIX}/posts/{post.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 409

    db_session.refresh(post)
    assert post.like_count == 1


def test_unlike_post_decrements_count(client, db_session):
    token, user_id = _register_and_login(client, db_session)
    board = _create_board(db_session)
    post = _create_post(db_session, user_id, board.id)

    client.post(
        f"{LIKES_PREFIX}/posts/{post.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    resp = client.delete(
        f"{LIKES_PREFIX}/posts/{post.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200

    db_session.refresh(post)
    assert post.like_count == 0


def test_unlike_post_not_liked_returns_404(client, db_session):
    token, user_id = _register_and_login(client, db_session)
    board = _create_board(db_session)
    post = _create_post(db_session, user_id, board.id)

    resp = client.delete(
        f"{LIKES_PREFIX}/posts/{post.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404


def test_unlike_then_like_again_succeeds(client, db_session):
    token, user_id = _register_and_login(client, db_session)
    board = _create_board(db_session)
    post = _create_post(db_session, user_id, board.id)

    client.post(
        f"{LIKES_PREFIX}/posts/{post.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    client.delete(
        f"{LIKES_PREFIX}/posts/{post.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    resp = client.post(
        f"{LIKES_PREFIX}/posts/{post.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200

    db_session.refresh(post)
    assert post.like_count == 1


def test_like_nonexistent_post_returns_404(client, db_session):
    token, user_id = _register_and_login(client, db_session)

    resp = client.post(
        f"{LIKES_PREFIX}/posts/00000000-0000-0000-0000-000000000000",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404


# ── Comment likes ────────────────────────────────────────────


def test_like_comment_success_and_increments_count(client, db_session):
    token, user_id = _register_and_login(client, db_session)
    board = _create_board(db_session)
    post = _create_post(db_session, user_id, board.id)
    comment = _create_comment(db_session, user_id, post.id)
    assert comment.like_count == 0

    resp = client.post(
        f"{LIKES_PREFIX}/comments/{comment.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200

    db_session.refresh(comment)
    assert comment.like_count == 1


def test_like_comment_duplicate_returns_409(client, db_session):
    token, user_id = _register_and_login(client, db_session)
    board = _create_board(db_session)
    post = _create_post(db_session, user_id, board.id)
    comment = _create_comment(db_session, user_id, post.id)

    client.post(
        f"{LIKES_PREFIX}/comments/{comment.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    resp = client.post(
        f"{LIKES_PREFIX}/comments/{comment.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 409

    db_session.refresh(comment)
    assert comment.like_count == 1


def test_unlike_comment_decrements_count(client, db_session):
    token, user_id = _register_and_login(client, db_session)
    board = _create_board(db_session)
    post = _create_post(db_session, user_id, board.id)
    comment = _create_comment(db_session, user_id, post.id)

    client.post(
        f"{LIKES_PREFIX}/comments/{comment.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    resp = client.delete(
        f"{LIKES_PREFIX}/comments/{comment.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200

    db_session.refresh(comment)
    assert comment.like_count == 0


def test_unlike_comment_not_liked_returns_404(client, db_session):
    token, user_id = _register_and_login(client, db_session)
    board = _create_board(db_session)
    post = _create_post(db_session, user_id, board.id)
    comment = _create_comment(db_session, user_id, post.id)

    resp = client.delete(
        f"{LIKES_PREFIX}/comments/{comment.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404
