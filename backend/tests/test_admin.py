"""
Admin 路由集成测试：stats / users / boards 管理

使用 AsyncClient + 内存 SQLite 替代真实 Postgres。
"""

import uuid

import pytest
import pytest_asyncio
from fastapi import status
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import get_db
from app.main import app
from app.models.base import Base
from app.models.user import User

SQLALCHEMY_DATABASE_URL = "sqlite:///test_admin.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

API_PREFIX = "/api/v1"
AUTH_PREFIX = f"{API_PREFIX}/auth"


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


def _register_and_login_sync(db, username="testuser", email="test@example.com"):
    """同步注册用户并返回 (user_id, role)。"""
    from app.utils.security import hash_password

    user = User(
        username=username,
        email=email,
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


async def _login(client: AsyncClient, account: str, password: str = "securepass123"):
    resp = await client.post(
        f"{AUTH_PREFIX}/login",
        json={"account": account, "password": password},
    )
    return resp.json()["data"]["access_token"]


async def _get_admin_client(client: AsyncClient, db_session) -> AsyncClient:
    """创建一个带 admin token 的客户端（复用同一个 transport）。"""
    admin_user = _register_and_login_sync(
        db_session, "admin_test", "admin_test@example.com"
    )
    admin_user.role = "admin"
    db_session.add(admin_user)
    db_session.commit()

    token = await _login(client, "admin_test")
    transport = ASGITransport(app=app)
    admin_client = AsyncClient(
        transport=transport,
        base_url="http://test",
        headers={"Authorization": f"Bearer {token}"},
    )
    return admin_client


# ---------- stats ----------


@pytest.mark.asyncio
async def test_admin_stats_unauthorized(client: AsyncClient):
    resp = await client.get(f"{API_PREFIX}/admin/stats")
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_get_admin_stats(client: AsyncClient, db_session):
    _register_and_login_sync(db_session, "statsuser", "stats@example.com")

    admin_client = await _get_admin_client(client, db_session)
    resp = await admin_client.get(f"{API_PREFIX}/admin/stats")
    assert resp.status_code == status.HTTP_200_OK
    body = resp.json()
    assert body["code"] == 200
    data = body["data"]
    assert data["total_users"] >= 1
    assert data["total_posts"] >= 0
    assert data["total_comments"] >= 0
    assert "new_posts_today" in data


# ---------- boards ----------


TEST_BOARD = {
    "name": "Test Board",
    "slug": "test-board",
    "description": "A test board",
    "sort_order": 1,
}


@pytest.mark.asyncio
async def test_board_lifecycle(client: AsyncClient, db_session):
    admin_client = await _get_admin_client(client, db_session)

    # Create
    resp = await admin_client.post(f"{API_PREFIX}/admin/boards", json=TEST_BOARD)
    assert resp.status_code == status.HTTP_201_CREATED
    body = resp.json()
    assert body["code"] == 200
    board = body["data"]
    board_id = board["id"]
    assert board["name"] == "Test Board"
    assert board["slug"] == "test-board"

    # Update
    resp = await admin_client.patch(
        f"{API_PREFIX}/admin/boards/{board_id}",
        json={"name": "Updated Board"},
    )
    assert resp.status_code == status.HTTP_200_OK
    updated = resp.json()["data"]
    assert updated["name"] == "Updated Board"

    # Delete
    resp = await admin_client.delete(f"{API_PREFIX}/admin/boards/{board_id}")
    assert resp.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.asyncio
async def test_create_board_duplicate_slug(client: AsyncClient, db_session):
    admin_client = await _get_admin_client(client, db_session)

    await admin_client.post(f"{API_PREFIX}/admin/boards", json=TEST_BOARD)
    resp = await admin_client.post(f"{API_PREFIX}/admin/boards", json=TEST_BOARD)
    assert resp.status_code == status.HTTP_400_BAD_REQUEST
    assert "slug" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_edit_nonexistent_board(client: AsyncClient, db_session):
    admin_client = await _get_admin_client(client, db_session)

    resp = await admin_client.patch(
        f"{API_PREFIX}/admin/boards/{uuid.uuid4()}",
        json={"name": "Ghost"},
    )
    assert resp.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_delete_nonexistent_board(client: AsyncClient, db_session):
    admin_client = await _get_admin_client(client, db_session)

    resp = await admin_client.delete(f"{API_PREFIX}/admin/boards/{uuid.uuid4()}")
    assert resp.status_code == status.HTTP_404_NOT_FOUND


# ---------- users ----------


@pytest.mark.asyncio
async def test_admin_list_users(client: AsyncClient, db_session):
    _register_and_login_sync(db_session, "ulist1", "ulist1@example.com")
    _register_and_login_sync(db_session, "ulist2", "ulist2@example.com")

    admin_client = await _get_admin_client(client, db_session)
    resp = await admin_client.get(
        f"{API_PREFIX}/admin/users", params={"page": 1, "page_size": 10}
    )
    assert resp.status_code == status.HTTP_200_OK
    body = resp.json()
    assert body["code"] == 200
    data = body["data"]
    assert "items" in data
    assert "pagination" in data
    assert len(data["items"]) >= 2


@pytest.mark.asyncio
async def test_admin_list_users_requires_admin(client: AsyncClient, db_session):
    _register_and_login_sync(db_session, "normie", "normie@example.com")
    token = await _login(client, "normie")

    resp = await client.get(
        f"{API_PREFIX}/admin/users",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_update_user_status_ban(client: AsyncClient, db_session):
    user = _register_and_login_sync(db_session, "victim", "victim@example.com")
    admin_client = await _get_admin_client(client, db_session)

    resp = await admin_client.patch(
        f"{API_PREFIX}/admin/users/{user.id}/status",
        json={"status": "banned"},
    )
    assert resp.status_code == status.HTTP_200_OK
    assert resp.json()["data"]["status"] == "banned"


@pytest.mark.asyncio
async def test_update_user_status_not_found(client: AsyncClient, db_session):
    admin_client = await _get_admin_client(client, db_session)

    resp = await admin_client.patch(
        f"{API_PREFIX}/admin/users/{uuid.uuid4()}/status",
        json={"status": "banned"},
    )
    assert resp.status_code == status.HTTP_404_NOT_FOUND
