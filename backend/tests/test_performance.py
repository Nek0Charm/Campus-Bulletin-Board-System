"""
性能测试 — 批量数据下的响应时间基准

验证关键接口在数据量增大时仍在可接受时间内返回结果。
基准阈值保守设置（SQLite 环境），生产 Postgres 下预期更快。
"""

import time
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
from app.models.comment import Comment
from app.models.post import Post
from app.models.user import User
from app.services.email_service import EmailService
from app.utils.security import hash_password

SQLALCHEMY_DATABASE_URL = "sqlite:///test_performance.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

POSTS_URL = "/api/v1/posts"
COMMENTS_URL = "/api/v1/comments"
SEARCH_URL = "/api/v1/search/posts"


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


# ── 数据工厂 ──────────────────────────────────────────────────────────────────


def _seed_user(db, username="perf_user") -> User:
    user = User(
        username=username,
        email=f"{username}@perf.com",
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


def _seed_board(db, slug="perf-board") -> Board:
    board = Board(name="Perf Board", slug=slug, sort_order=0)
    db.add(board)
    db.commit()
    db.refresh(board)
    return board


def _seed_posts(db, user: User, board: Board, n: int) -> list[Post]:
    posts = []
    for i in range(n):
        p = Post(
            title=f"Performance Post {i}",
            content=f"Content for post {i}. " * 10,
            author_id=user.id,
            board_id=board.id,
            published_at=datetime.now(timezone.utc),
        )
        db.add(p)
        posts.append(p)
    db.commit()
    for p in posts:
        db.refresh(p)
    return posts


def _seed_comments(db, user: User, post: Post, n: int) -> list[Comment]:
    comments = []
    for i in range(n):
        c = Comment(
            post_id=post.id,
            author_id=user.id,
            content=f"Comment {i}",
        )
        db.add(c)
        comments.append(c)
    post.comment_count = n
    db.commit()
    for c in comments:
        db.refresh(c)
    return comments


# ── 性能基准 ──────────────────────────────────────────────────────────────────


def test_list_50_posts_under_2s(client, db_session):
    """50 条帖子的列表接口应在 2 秒内返回。"""
    user = _seed_user(db_session)
    board = _seed_board(db_session)
    _seed_posts(db_session, user, board, 50)

    start = time.perf_counter()
    resp = client.get(f"{POSTS_URL}/", params={"page": 1, "page_size": 20})
    elapsed = time.perf_counter() - start

    assert resp.status_code == 200
    assert resp.json()["data"]["pagination"]["total"] == 50
    assert elapsed < 2.0, f"list posts took {elapsed:.2f}s, expected < 2s"


def test_list_posts_second_page_performance(client, db_session):
    """第 2 页分页响应时间应与第 1 页相当（< 2s）。"""
    user = _seed_user(db_session, "perf2")
    board = _seed_board(db_session, "perf2-board")
    _seed_posts(db_session, user, board, 50)

    start = time.perf_counter()
    resp = client.get(f"{POSTS_URL}/", params={"page": 3, "page_size": 10})
    elapsed = time.perf_counter() - start

    assert resp.status_code == 200
    assert len(resp.json()["data"]["items"]) == 10
    assert elapsed < 2.0


def test_search_across_50_posts_under_3s(client, db_session):
    """50 条帖子中关键字搜索应在 3 秒内完成。"""
    user = _seed_user(db_session, "search_user")
    board = _seed_board(db_session, "search-board")
    posts = _seed_posts(db_session, user, board, 50)
    # 使部分帖子包含目标关键字
    for p in posts[:10]:
        p.title = f"UniqueKeyword {p.title}"
    db_session.commit()

    start = time.perf_counter()
    resp = client.get(f"{SEARCH_URL}", params={"q": "UniqueKeyword"})
    elapsed = time.perf_counter() - start

    assert resp.status_code == 200
    assert resp.json()["data"]["pagination"]["total"] == 10
    assert elapsed < 3.0, f"search took {elapsed:.2f}s, expected < 3s"


def test_list_100_comments_under_3s(client, db_session):
    """单帖 100 条评论的列表接口应在 3 秒内返回。"""
    user = _seed_user(db_session, "cmt_user")
    board = _seed_board(db_session, "cmt-board")
    post = _seed_posts(db_session, user, board, 1)[0]
    _seed_comments(db_session, user, post, 100)

    start = time.perf_counter()
    resp = client.get(
        f"{COMMENTS_URL}/", params={"post_id": str(post.id), "page_size": 20}
    )
    elapsed = time.perf_counter() - start

    assert resp.status_code == 200
    assert resp.json()["data"]["pagination"]["total"] == 100
    assert elapsed < 3.0, f"list comments took {elapsed:.2f}s, expected < 3s"


def test_repeated_single_post_fetch_under_1s(client, db_session):
    """单帖详情接口连续请求 10 次，每次应在 1 秒内返回。"""
    user = _seed_user(db_session, "fetch_user")
    board = _seed_board(db_session, "fetch-board")
    post = _seed_posts(db_session, user, board, 1)[0]

    for _ in range(10):
        start = time.perf_counter()
        resp = client.get(f"{POSTS_URL}/{post.id}")
        elapsed = time.perf_counter() - start
        assert resp.status_code == 200
        assert elapsed < 1.0, f"single post fetch took {elapsed:.2f}s"
