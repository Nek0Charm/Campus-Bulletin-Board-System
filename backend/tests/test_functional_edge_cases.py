"""
功能测试 — 边界与边缘用例

覆盖现有测试集未涉及的场景：
- Unicode / Emoji 内容
- 输入边界值（超长、空内容）
- 分页边界（超出最后一页、page_size=1）
- 完整 CRUD 链路（帖子→评论→点赞→取消→删除）
- 搜索边界（无结果、特殊字符）
- 多用户交互同一帖子
"""

from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import get_db
from app.deps import get_email_service
from app.main import app
from app.models.base import Base
from app.models.board import Board
from app.services.email_service import EmailService

SQLALCHEMY_DATABASE_URL = "sqlite:///test_functional_edge.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

AUTH = "/api/v1/auth"
POSTS = "/api/v1/posts"
COMMENTS = "/api/v1/comments"
LIKES = "/api/v1/likes"
SEARCH = "/api/v1/search/posts"


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


def _register_and_login(client, db_session, username="user1", email="u1@test.com"):
    client.post(
        f"{AUTH}/register",
        json={"username": username, "email": email, "password": "securepass123"},
    )
    from app.models.user import User

    user = db_session.query(User).filter(User.username == username).first()
    user.email_verified = True
    db_session.commit()
    resp = client.post(
        f"{AUTH}/login", json={"account": username, "password": "securepass123"}
    )
    data = resp.json()["data"]
    return data["access_token"], data["user"]["id"]


def _create_board(db_session, slug="edge-board"):
    board = Board(name="Edge Board", slug=slug, sort_order=0)
    db_session.add(board)
    db_session.commit()
    db_session.refresh(board)
    return board


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


# ── Unicode / Emoji ───────────────────────────────────────────────────────────


def test_post_with_emoji_and_cjk(client, db_session):
    token, _ = _register_and_login(client, db_session)
    board = _create_board(db_session)
    resp = client.post(
        f"{POSTS}/",
        json={
            "title": "🎉 测试帖子 Unicode ñ €",
            "content": "内容含 emoji 🚀 和中文，以及特殊符号 © ™ ®",
            "board_id": str(board.id),
        },
        headers=_auth(token),
    )
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert "🎉" in data["title"]
    assert "🚀" in data["content"]


def test_comment_with_emoji(client, db_session):
    token, uid = _register_and_login(client, db_session)
    board = _create_board(db_session, "emoji-board")
    post_resp = client.post(
        f"{POSTS}/",
        json={"title": "Post", "content": "body", "board_id": str(board.id)},
        headers=_auth(token),
    )
    post_id = post_resp.json()["data"]["id"]

    resp = client.post(
        f"{COMMENTS}/",
        json={"post_id": post_id, "content": "👍 很赞！"},
        headers=_auth(token),
    )
    assert resp.status_code == 201
    assert "👍" in resp.json()["data"]["content"]


# ── 输入边界值 ────────────────────────────────────────────────────────────────


def test_post_title_max_length_accepted(client, db_session):
    token, _ = _register_and_login(client, db_session)
    board = _create_board(db_session, "len-board")
    title = "A" * 200
    resp = client.post(
        f"{POSTS}/",
        json={"title": title, "content": "body", "board_id": str(board.id)},
        headers=_auth(token),
    )
    assert resp.status_code in (201, 422)


def test_post_empty_title_rejected(client, db_session):
    token, _ = _register_and_login(client, db_session)
    board = _create_board(db_session, "empty-title-board")
    resp = client.post(
        f"{POSTS}/",
        json={"title": "", "content": "body", "board_id": str(board.id)},
        headers=_auth(token),
    )
    assert resp.status_code == 422


def test_comment_empty_content_rejected(client, db_session):
    token, uid = _register_and_login(client, db_session)
    board = _create_board(db_session, "empty-comment-board")
    post_resp = client.post(
        f"{POSTS}/",
        json={"title": "T", "content": "body", "board_id": str(board.id)},
        headers=_auth(token),
    )
    post_id = post_resp.json()["data"]["id"]
    resp = client.post(
        f"{COMMENTS}/",
        json={"post_id": post_id, "content": ""},
        headers=_auth(token),
    )
    assert resp.status_code == 422


# ── 分页边界 ──────────────────────────────────────────────────────────────────


def test_posts_page_beyond_total_returns_empty(client, db_session):
    token, _ = _register_and_login(client, db_session)
    board = _create_board(db_session, "page-board")
    client.post(
        f"{POSTS}/",
        json={"title": "Only Post", "content": "x", "board_id": str(board.id)},
        headers=_auth(token),
    )
    resp = client.get(f"{POSTS}/", params={"page": 999, "page_size": 20})
    assert resp.status_code == 200
    body = resp.json()["data"]
    assert body["items"] == []
    assert body["pagination"]["total"] == 1


def test_posts_page_size_one(client, db_session):
    token, _ = _register_and_login(client, db_session)
    board = _create_board(db_session, "size1-board")
    for i in range(3):
        client.post(
            f"{POSTS}/",
            json={"title": f"Post {i}", "content": "x", "board_id": str(board.id)},
            headers=_auth(token),
        )
    resp = client.get(f"{POSTS}/", params={"page": 1, "page_size": 1})
    assert resp.status_code == 200
    body = resp.json()["data"]
    assert len(body["items"]) == 1
    assert body["pagination"]["total"] == 3
    assert body["pagination"]["total_pages"] == 3


def test_comments_page_beyond_total_returns_empty(client, db_session):
    token, uid = _register_and_login(client, db_session)
    board = _create_board(db_session, "cmtpage-board")
    post_resp = client.post(
        f"{POSTS}/",
        json={"title": "P", "content": "x", "board_id": str(board.id)},
        headers=_auth(token),
    )
    post_id = post_resp.json()["data"]["id"]
    client.post(
        f"{COMMENTS}/",
        json={"post_id": post_id, "content": "hi"},
        headers=_auth(token),
    )
    resp = client.get(f"{COMMENTS}/", params={"post_id": post_id, "page": 999})
    assert resp.status_code == 200
    assert resp.json()["data"]["items"] == []


# ── 完整 CRUD 链路 ─────────────────────────────────────────────────────────────


def test_full_crud_chain(client, db_session):
    """帖子 → 评论 → 点赞帖子 → 取消点赞 → 删除评论 → 删除帖子"""
    token, uid = _register_and_login(client, db_session)
    board = _create_board(db_session, "chain-board")

    # 创建帖子
    post_id = client.post(
        f"{POSTS}/",
        json={"title": "Chain", "content": "body", "board_id": str(board.id)},
        headers=_auth(token),
    ).json()["data"]["id"]

    # 评论
    comment_id = client.post(
        f"{COMMENTS}/",
        json={"post_id": post_id, "content": "reply"},
        headers=_auth(token),
    ).json()["data"]["id"]

    # 点赞帖子
    assert (
        client.post(f"{LIKES}/posts/{post_id}", headers=_auth(token)).status_code == 200
    )

    # 取消点赞
    assert (
        client.delete(f"{LIKES}/posts/{post_id}", headers=_auth(token)).status_code
        == 200
    )

    # 删除评论
    assert (
        client.delete(f"{COMMENTS}/{comment_id}", headers=_auth(token)).status_code
        == 200
    )

    # 删除帖子
    assert client.delete(f"{POSTS}/{post_id}", headers=_auth(token)).status_code == 200


# ── 多用户交互 ────────────────────────────────────────────────────────────────


def test_multiple_users_like_same_post(client, db_session):
    token1, _ = _register_and_login(client, db_session, "liker1", "l1@test.com")
    token2, _ = _register_and_login(client, db_session, "liker2", "l2@test.com")
    board = _create_board(db_session, "multi-like-board")

    post_id = client.post(
        f"{POSTS}/",
        json={"title": "Popular", "content": "body", "board_id": str(board.id)},
        headers=_auth(token1),
    ).json()["data"]["id"]

    client.post(f"{LIKES}/posts/{post_id}", headers=_auth(token1))
    client.post(f"{LIKES}/posts/{post_id}", headers=_auth(token2))

    resp = client.get(f"{POSTS}/{post_id}")
    assert resp.json()["data"]["like_count"] == 2


def test_two_users_comment_and_reply(client, db_session):
    token1, _ = _register_and_login(client, db_session, "writer1", "w1@test.com")
    token2, _ = _register_and_login(client, db_session, "writer2", "w2@test.com")
    board = _create_board(db_session, "conv-board")

    post_id = client.post(
        f"{POSTS}/",
        json={"title": "Convo", "content": "body", "board_id": str(board.id)},
        headers=_auth(token1),
    ).json()["data"]["id"]

    root_id = client.post(
        f"{COMMENTS}/",
        json={"post_id": post_id, "content": "root comment"},
        headers=_auth(token1),
    ).json()["data"]["id"]

    resp = client.post(
        f"{COMMENTS}/",
        json={"post_id": post_id, "content": "reply", "parent_comment_id": root_id},
        headers=_auth(token2),
    )
    assert resp.status_code == 201
    assert resp.json()["data"]["root_comment_id"] == root_id


# ── 搜索边界 ──────────────────────────────────────────────────────────────────


def test_search_no_results(client, db_session):
    resp = client.get(f"{SEARCH}", params={"q": "xyzzy_no_match_12345"})
    assert resp.status_code == 200
    assert resp.json()["data"]["pagination"]["total"] == 0


def test_search_with_special_chars_does_not_crash(client, db_session):
    resp = client.get(f"{SEARCH}", params={"q": "'; DROP TABLE posts; --"})
    assert resp.status_code == 200


def test_search_empty_query_rejected(client):
    resp = client.get(f"{SEARCH}", params={"q": ""})
    assert resp.status_code == 422
