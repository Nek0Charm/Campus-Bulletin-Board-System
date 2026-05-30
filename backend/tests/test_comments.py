"""
Comments 路由集成测试：发布、回复、列表（楼栋结构）、编辑、删除，以及 comment_count 同步。
"""

from datetime import datetime, timezone
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
from app.models.post import Post
from app.services.email_service import EmailService

SQLALCHEMY_DATABASE_URL = "sqlite:///test_comments.db"

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
):
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


def _create_board(db_session):
    board = Board(name="Test Board", slug="test-board", sort_order=0)
    db_session.add(board)
    db_session.commit()
    db_session.refresh(board)
    return board


def _create_post(db_session, author_id):
    post = Post(
        title="Test Post",
        content="Hello",
        author_id=UUID(author_id),
        board_id=_create_board(db_session).id,
        published_at=datetime.now(timezone.utc),
    )
    db_session.add(post)
    db_session.commit()
    db_session.refresh(post)
    return post


# ── 发布评论 ──────────────────────────────────────────────────


def test_create_comment_requires_auth(client, db_session):
    token, uid = _register_and_login(client, db_session)
    post = _create_post(db_session, uid)

    resp = client.post(
        API_PREFIX + "/", json={"post_id": str(post.id), "content": "hi"}
    )
    assert resp.status_code == 401


def test_create_root_comment_increments_comment_count(client, db_session):
    token, uid = _register_and_login(client, db_session)
    post = _create_post(db_session, uid)

    resp = client.post(
        API_PREFIX + "/",
        json={"post_id": str(post.id), "content": "Root comment"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["root_comment_id"] is None
    assert data["parent_comment_id"] is None

    db_session.refresh(post)
    assert post.comment_count == 1


def test_create_reply_sets_root_and_parent(client, db_session):
    token, uid = _register_and_login(client, db_session)
    post = _create_post(db_session, uid)

    root_resp = client.post(
        API_PREFIX + "/",
        json={"post_id": str(post.id), "content": "Root"},
        headers={"Authorization": f"Bearer {token}"},
    )
    root_id = root_resp.json()["data"]["id"]

    reply_resp = client.post(
        API_PREFIX + "/",
        json={
            "post_id": str(post.id),
            "content": "Reply",
            "parent_comment_id": root_id,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert reply_resp.status_code == 201
    data = reply_resp.json()["data"]
    assert data["root_comment_id"] == root_id
    assert data["parent_comment_id"] == root_id


def test_reply_to_reply_keeps_original_root(client, db_session):
    token, uid = _register_and_login(client, db_session)
    post = _create_post(db_session, uid)

    root = client.post(
        API_PREFIX + "/",
        json={"post_id": str(post.id), "content": "Root"},
        headers={"Authorization": f"Bearer {token}"},
    ).json()["data"]

    reply = client.post(
        API_PREFIX + "/",
        json={
            "post_id": str(post.id),
            "content": "Reply1",
            "parent_comment_id": root["id"],
        },
        headers={"Authorization": f"Bearer {token}"},
    ).json()["data"]

    reply2 = client.post(
        API_PREFIX + "/",
        json={
            "post_id": str(post.id),
            "content": "Reply2",
            "parent_comment_id": reply["id"],
        },
        headers={"Authorization": f"Bearer {token}"},
    ).json()["data"]

    assert reply2["root_comment_id"] == root["id"]
    assert reply2["parent_comment_id"] == reply["id"]


# ── 评论列表（楼栋结构） ───────────────────────────────────────


def test_list_comments_floor_structure(client, db_session):
    token, uid = _register_and_login(client, db_session)
    post = _create_post(db_session, uid)

    root = client.post(
        API_PREFIX + "/",
        json={"post_id": str(post.id), "content": "Floor 1"},
        headers={"Authorization": f"Bearer {token}"},
    ).json()["data"]
    client.post(
        API_PREFIX + "/",
        json={
            "post_id": str(post.id),
            "content": "Reply",
            "parent_comment_id": root["id"],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    # 第二个根评论
    client.post(
        API_PREFIX + "/",
        json={"post_id": str(post.id), "content": "Floor 2"},
        headers={"Authorization": f"Bearer {token}"},
    )

    resp = client.get(API_PREFIX + "/", params={"post_id": str(post.id)})
    assert resp.status_code == 200
    body = resp.json()["data"]
    assert body["pagination"]["total"] == 2  # 只计根评论

    floor1 = body["items"][0]
    assert floor1["content"] == "Floor 1"
    assert len(floor1["replies"]) == 1
    assert floor1["replies"][0]["content"] == "Reply"

    floor2 = body["items"][1]
    assert floor2["content"] == "Floor 2"
    assert len(floor2["replies"]) == 0


# ── 编辑评论 ──────────────────────────────────────────────────


def test_update_comment_by_author(client, db_session):
    token, uid = _register_and_login(client, db_session)
    post = _create_post(db_session, uid)
    comment = client.post(
        API_PREFIX + "/",
        json={"post_id": str(post.id), "content": "Old"},
        headers={"Authorization": f"Bearer {token}"},
    ).json()["data"]

    resp = client.patch(
        f"{API_PREFIX}/{comment['id']}",
        json={"content": "New"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["content"] == "New"


def test_update_comment_by_other_returns_403(client, db_session):
    token, uid = _register_and_login(client, db_session)
    token2, _ = _register_and_login(
        client, db_session, username="other", email="other@example.com"
    )
    post = _create_post(db_session, uid)
    comment = client.post(
        API_PREFIX + "/",
        json={"post_id": str(post.id), "content": "Old"},
        headers={"Authorization": f"Bearer {token}"},
    ).json()["data"]

    resp = client.patch(
        f"{API_PREFIX}/{comment['id']}",
        json={"content": "Hack"},
        headers={"Authorization": f"Bearer {token2}"},
    )
    assert resp.status_code == 403


# ── 删除评论 ──────────────────────────────────────────────────


def test_delete_comment_decrements_comment_count(client, db_session):
    token, uid = _register_and_login(client, db_session)
    post = _create_post(db_session, uid)
    comment = client.post(
        API_PREFIX + "/",
        json={"post_id": str(post.id), "content": "To delete"},
        headers={"Authorization": f"Bearer {token}"},
    ).json()["data"]

    db_session.refresh(post)
    assert post.comment_count == 1

    resp = client.delete(
        f"{API_PREFIX}/{comment['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200

    db_session.refresh(post)
    assert post.comment_count == 0


def test_delete_comment_by_other_returns_403(client, db_session):
    token, uid = _register_and_login(client, db_session)
    token2, _ = _register_and_login(
        client, db_session, username="other2", email="other2@example.com"
    )
    post = _create_post(db_session, uid)
    comment = client.post(
        API_PREFIX + "/",
        json={"post_id": str(post.id), "content": "Mine"},
        headers={"Authorization": f"Bearer {token}"},
    ).json()["data"]

    resp = client.delete(
        f"{API_PREFIX}/{comment['id']}",
        headers={"Authorization": f"Bearer {token2}"},
    )
    assert resp.status_code == 403


def test_deleted_comment_not_in_list(client, db_session):
    token, uid = _register_and_login(client, db_session)
    post = _create_post(db_session, uid)
    comment = client.post(
        API_PREFIX + "/",
        json={"post_id": str(post.id), "content": "Gone"},
        headers={"Authorization": f"Bearer {token}"},
    ).json()["data"]
    client.delete(
        f"{API_PREFIX}/{comment['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )

    resp = client.get(API_PREFIX + "/", params={"post_id": str(post.id)})
    assert resp.json()["data"]["pagination"]["total"] == 0


# ── 内容校验 ──────────────────────────────────────────────────


def test_create_comment_empty_content(client, db_session):
    token, uid = _register_and_login(client, db_session)
    post = _create_post(db_session, uid)
    resp = client.post(
        API_PREFIX + "/",
        json={"post_id": str(post.id), "content": ""},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 422


def test_create_comment_content_too_long(client, db_session):
    token, uid = _register_and_login(client, db_session)
    post = _create_post(db_session, uid)
    resp = client.post(
        API_PREFIX + "/",
        json={"post_id": str(post.id), "content": "x" * 10001},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 422
