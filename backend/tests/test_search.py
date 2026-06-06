"""
Search 路由集成测试：关键词、板块/时间筛选、排序与隐藏帖子过滤。

测试使用 SQLite 回退搜索逻辑，生产 PostgreSQL 走 tsvector + GIN 索引。
"""

from datetime import datetime, timezone
from uuid import UUID

import pytest
import pytest_asyncio
from fastapi import status
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import get_db
from app.main import app
from app.models.base import Base
from app.models.board import Board
from app.models.post import Post
from app.models.user import User
from app.utils.security import hash_password

SQLALCHEMY_DATABASE_URL = "sqlite:///test_search.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

API_PREFIX = "/api/v1"
AUTH_PREFIX = f"{API_PREFIX}/auth"
POSTS_URL = f"{API_PREFIX}/posts/"
SEARCH_URL = f"{API_PREFIX}/search/posts"


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


@pytest.fixture()
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest_asyncio.fixture()
async def client():
    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


def _create_user(db, username: str = "searcher") -> User:
    user = User(
        username=username,
        email=f"{username}@test.com",
        password_hash=hash_password("securepass123"),
        nickname=username,
        role="user",
        status="active",
        email_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _create_board(db, name: str, slug: str) -> Board:
    board = Board(name=name, slug=slug, description="test", sort_order=1)
    db.add(board)
    db.commit()
    db.refresh(board)
    return board


async def _login(client: AsyncClient, username: str) -> str:
    resp = await client.post(
        f"{AUTH_PREFIX}/login",
        json={"account": username, "password": "securepass123"},
    )
    return resp.json()["data"]["access_token"]


def _auth_client(token: str) -> AsyncClient:
    transport = ASGITransport(app=app)
    return AsyncClient(
        transport=transport,
        base_url="http://test",
        headers={"Authorization": f"Bearer {token}"},
    )


async def _create_post(
    client: AsyncClient,
    db,
    *,
    title: str,
    content: str,
    board: Board,
    username: str = "searcher",
):
    if not db.query(User).filter(User.username == username).first():
        _create_user(db, username)
    token = await _login(client, username)
    async with _auth_client(token) as ac:
        resp = await ac.post(
            POSTS_URL,
            json={"title": title, "content": content, "board_id": str(board.id)},
        )
    assert resp.status_code == status.HTTP_201_CREATED
    post_id = resp.json()["data"]["id"]
    return db.query(Post).filter(Post.id == UUID(post_id)).first()


@pytest.mark.asyncio
async def test_search_posts_matches_chinese_keyword(client: AsyncClient, db_session):
    board = _create_board(db_session, "校园生活", "life")
    await _create_post(
        client,
        db_session,
        title="食堂午饭推荐",
        content="今天学校食堂的番茄牛腩很好吃",
        board=board,
    )
    await _create_post(
        client,
        db_session,
        title="课程安排",
        content="软件工程课程下周提交作业",
        board=board,
    )

    resp = await client.get(SEARCH_URL, params={"q": "食堂"})
    assert resp.status_code == status.HTTP_200_OK
    items = resp.json()["data"]["items"]
    assert len(items) == 1
    assert items[0]["title"] == "食堂午饭推荐"


@pytest.mark.asyncio
async def test_search_posts_filters_by_board(client: AsyncClient, db_session):
    board_a = _create_board(db_session, "失物招领", "lost")
    board_b = _create_board(db_session, "二手交易", "market")
    await _create_post(
        client,
        db_session,
        title="校园卡搜索测试",
        content="在图书馆捡到校园卡",
        board=board_a,
    )
    await _create_post(
        client,
        db_session,
        title="校园卡卡套转让",
        content="出售一个校园卡保护套",
        board=board_b,
    )

    resp = await client.get(
        SEARCH_URL, params={"q": "校园卡", "board_id": str(board_a.id)}
    )
    items = resp.json()["data"]["items"]
    assert len(items) == 1
    assert items[0]["board_id"] == str(board_a.id)


@pytest.mark.asyncio
async def test_search_posts_filters_by_date(client: AsyncClient, db_session):
    board = _create_board(db_session, "活动", "events")
    old_post = await _create_post(
        client,
        db_session,
        title="社团活动报名",
        content="活动搜索测试",
        board=board,
    )
    new_post = await _create_post(
        client,
        db_session,
        title="学院活动报名",
        content="活动搜索测试",
        board=board,
    )
    old_post.published_at = datetime(2026, 5, 20, tzinfo=timezone.utc)
    new_post.published_at = datetime(2026, 6, 3, tzinfo=timezone.utc)
    db_session.commit()

    resp = await client.get(
        SEARCH_URL,
        params={"q": "活动", "start_date": "2026-06-01", "end_date": "2026-06-05"},
    )
    items = resp.json()["data"]["items"]
    assert len(items) == 1
    assert items[0]["title"] == "学院活动报名"


@pytest.mark.asyncio
async def test_search_posts_sorts_by_hot(client: AsyncClient, db_session):
    board = _create_board(db_session, "讨论", "discuss")
    low = await _create_post(
        client,
        db_session,
        title="搜索排序低热度",
        content="搜索排序测试",
        board=board,
    )
    high = await _create_post(
        client,
        db_session,
        title="搜索排序高热度",
        content="搜索排序测试",
        board=board,
    )
    low.like_count = 1
    high.comment_count = 5
    db_session.commit()

    resp = await client.get(SEARCH_URL, params={"q": "搜索排序", "sort_by": "hot"})
    items = resp.json()["data"]["items"]
    assert items[0]["title"] == "搜索排序高热度"


@pytest.mark.asyncio
async def test_search_posts_excludes_hidden_posts(client: AsyncClient, db_session):
    board = _create_board(db_session, "公告", "notice")
    post = await _create_post(
        client,
        db_session,
        title="隐藏搜索结果",
        content="隐藏搜索测试",
        board=board,
    )
    post.status = "hidden"
    db_session.commit()

    resp = await client.get(SEARCH_URL, params={"q": "隐藏搜索"})
    assert resp.json()["data"]["items"] == []


@pytest.mark.asyncio
async def test_search_posts_rejects_invalid_date_range(client: AsyncClient):
    resp = await client.get(
        SEARCH_URL,
        params={"q": "活动", "start_date": "2026-06-05", "end_date": "2026-06-01"},
    )
    assert resp.status_code == status.HTTP_400_BAD_REQUEST
