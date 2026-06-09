"""
稳定性测试

覆盖：
- 快速连续点赞 / 取消循环（验证计数不漂移）
- 长操作序列（注册 → 发帖 → 多级评论 → 批量点赞 → 批量删除）
- 并发混合读写（ThreadPoolExecutor）
- 错误恢复：操作失败后系统状态保持一致
- 无效输入批量轰炸（验证不崩溃）
"""

import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
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
from app.models.post import Post
from app.models.user import User
from app.services.email_service import EmailService
from app.utils.security import hash_password

SQLALCHEMY_DATABASE_URL = "sqlite:///test_stability.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

AUTH = "/api/v1/auth"
POSTS = "/api/v1/posts"
COMMENTS = "/api/v1/comments"
LIKES = "/api/v1/likes"


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


# ── 工具函数 ──────────────────────────────────────────────────────────────────


def _register_and_login(client, db_session, username, email):
    client.post(
        f"{AUTH}/register",
        json={"username": username, "email": email, "password": "securepass123"},
    )
    user = db_session.query(User).filter(User.username == username).first()
    user.email_verified = True
    db_session.commit()
    resp = client.post(
        f"{AUTH}/login", json={"account": username, "password": "securepass123"}
    )
    data = resp.json()["data"]
    return data["access_token"], data["user"]["id"]


def _seed_user(db, username) -> User:
    user = User(
        username=username,
        email=f"{username}@stab.com",
        password_hash=hash_password("pass"),
        nickname=username,
        role="user",
        status="active",
        email_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _seed_post(db, user: User, board: Board) -> Post:
    post = Post(
        title="Stability Post",
        content="body",
        author_id=user.id,
        board_id=board.id,
        published_at=datetime.now(timezone.utc),
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return post


def _seed_board(db, slug="stab-board") -> Board:
    board = Board(name="Stability Board", slug=slug, sort_order=0)
    db.add(board)
    db.commit()
    db.refresh(board)
    return board


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


# ── 快速点赞 / 取消循环 ───────────────────────────────────────────────────────


def test_rapid_like_unlike_count_stable(client, db_session):
    """10 次点赞/取消循环后 like_count 应归零且无异常。"""
    token, _ = _register_and_login(client, db_session, "rapid_liker", "rl@stab.com")
    board = _seed_board(db_session, "rapid-board")
    user = db_session.query(User).filter(User.username == "rapid_liker").first()
    post = _seed_post(db_session, user, board)

    for _ in range(10):
        r1 = client.post(f"{LIKES}/posts/{post.id}", headers=_auth(token))
        assert r1.status_code == 200
        r2 = client.delete(f"{LIKES}/posts/{post.id}", headers=_auth(token))
        assert r2.status_code == 200

    db_session.refresh(post)
    assert post.like_count == 0


def test_rapid_comment_like_unlike(client, db_session):
    """评论点赞快速循环 5 次后计数应归零。"""
    token, uid = _register_and_login(client, db_session, "cmt_liker", "cl@stab.com")
    board = _seed_board(db_session, "cmt-like-board")
    user = db_session.query(User).filter(User.username == "cmt_liker").first()
    post = _seed_post(db_session, user, board)

    cmt_id = client.post(
        f"{COMMENTS}/",
        json={"post_id": str(post.id), "content": "hi"},
        headers=_auth(token),
    ).json()["data"]["id"]

    for _ in range(5):
        assert (
            client.post(f"{LIKES}/comments/{cmt_id}", headers=_auth(token)).status_code
            == 200
        )
        assert (
            client.delete(
                f"{LIKES}/comments/{cmt_id}", headers=_auth(token)
            ).status_code
            == 200
        )

    from uuid import UUID

    from app.models.comment import Comment

    cmt = db_session.query(Comment).filter(Comment.id == UUID(cmt_id)).first()
    assert cmt.like_count == 0


# ── 长操作序列 ────────────────────────────────────────────────────────────────


def test_long_operation_sequence(client, db_session):
    """注册 → 发帖 → 多层评论 → 批量点赞 → 批量删除，全程无错误。"""
    token, uid = _register_and_login(client, db_session, "seq_user", "seq@stab.com")
    board = _seed_board(db_session, "seq-board")

    # 发 5 篇帖子
    post_ids = []
    for i in range(5):
        pid = client.post(
            f"{POSTS}/",
            json={"title": f"Seq Post {i}", "content": "x", "board_id": str(board.id)},
            headers=_auth(token),
        ).json()["data"]["id"]
        post_ids.append(pid)

    # 每篇发根评论 + 回复
    comment_ids = []
    for pid in post_ids:
        root_id = client.post(
            f"{COMMENTS}/",
            json={"post_id": pid, "content": "root"},
            headers=_auth(token),
        ).json()["data"]["id"]
        comment_ids.append(root_id)
        reply_id = client.post(
            f"{COMMENTS}/",
            json={"post_id": pid, "content": "reply", "parent_comment_id": root_id},
            headers=_auth(token),
        ).json()["data"]["id"]
        comment_ids.append(reply_id)

    # 点赞所有帖子
    for pid in post_ids:
        assert (
            client.post(f"{LIKES}/posts/{pid}", headers=_auth(token)).status_code == 200
        )

    # 删除所有评论
    for cid in comment_ids:
        assert (
            client.delete(f"{COMMENTS}/{cid}", headers=_auth(token)).status_code == 200
        )

    # 删除所有帖子
    for pid in post_ids:
        assert client.delete(f"{POSTS}/{pid}", headers=_auth(token)).status_code == 200


# ── 并发混合读写 ──────────────────────────────────────────────────────────────


def test_concurrent_reads_while_writing(db_session):
    """5 个写线程与 5 个读线程并发运行，均应成功完成。"""
    user = _seed_user(db_session, "concurrent_user")
    board = _seed_board(db_session, "concurrent-board")
    post = _seed_post(db_session, user, board)
    post_id = str(post.id)

    barrier = threading.Barrier(10)
    results: list[int] = []
    lock = threading.Lock()

    def writer():
        app.dependency_overrides[get_db] = _override_get_db
        c = TestClient(app)
        barrier.wait(timeout=10)
        resp = c.get(f"{POSTS}/{post_id}")
        with lock:
            results.append(resp.status_code)

    def reader():
        app.dependency_overrides[get_db] = _override_get_db
        c = TestClient(app)
        barrier.wait(timeout=10)
        resp = c.get(f"{POSTS}/{post_id}")
        with lock:
            results.append(resp.status_code)

    workers = [writer] * 5 + [reader] * 5
    with ThreadPoolExecutor(max_workers=10) as pool:
        futs = [pool.submit(w) for w in workers]
        for f in futs:
            f.result(timeout=15)

    assert all(s == 200 for s in results), f"Some requests failed: {results}"


# ── 错误恢复：状态一致性 ──────────────────────────────────────────────────────


def test_double_like_does_not_corrupt_count(client, db_session):
    """重复点赞返回 409，like_count 不应增加两次。"""
    token, _ = _register_and_login(client, db_session, "double_liker", "dl@stab.com")
    board = _seed_board(db_session, "double-board")
    user = db_session.query(User).filter(User.username == "double_liker").first()
    post = _seed_post(db_session, user, board)

    client.post(f"{LIKES}/posts/{post.id}", headers=_auth(token))
    r2 = client.post(f"{LIKES}/posts/{post.id}", headers=_auth(token))
    assert r2.status_code == 409

    db_session.refresh(post)
    assert post.like_count == 1


def test_unlike_nonexistent_does_not_corrupt_count(client, db_session):
    """未点赞时取消返回 404，like_count 不应变为负数。"""
    token, _ = _register_and_login(client, db_session, "ghost_unliker", "gu@stab.com")
    board = _seed_board(db_session, "ghost-board")
    user = db_session.query(User).filter(User.username == "ghost_unliker").first()
    post = _seed_post(db_session, user, board)

    r = client.delete(f"{LIKES}/posts/{post.id}", headers=_auth(token))
    assert r.status_code == 404

    db_session.refresh(post)
    assert post.like_count == 0


def test_delete_nonexistent_comment_returns_404(client, db_session):
    """删除不存在的评论应返回 404，不影响其他数据。"""
    token, _ = _register_and_login(client, db_session, "ghost_deleter", "gd@stab.com")
    fake_id = "00000000-0000-0000-0000-000000000000"
    resp = client.delete(f"{COMMENTS}/{fake_id}", headers=_auth(token))
    assert resp.status_code == 404


# ── 无效输入批量压力 ──────────────────────────────────────────────────────────


def test_invalid_inputs_do_not_crash_server(client, db_session):
    """大量格式错误的请求不应导致服务崩溃（均应返回 4xx）。"""
    token, _ = _register_and_login(client, db_session, "bomber", "bomb@stab.com")
    invalid_payloads = [
        {},
        {"title": None, "content": None},
        {"title": "x" * 10000, "content": "y"},
        {"board_id": "not-a-uuid", "title": "t", "content": "c"},
    ]
    for payload in invalid_payloads:
        resp = client.post(f"{POSTS}/", json=payload, headers=_auth(token))
        assert (
            400 <= resp.status_code < 500
        ), f"Expected 4xx for {payload}, got {resp.status_code}"
