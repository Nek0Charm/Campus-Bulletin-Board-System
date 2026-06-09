"""
Announcement 集成测试：公开列表 + 管理端 CRUD。

使用 AsyncClient + 内存 SQLite 替代真实 Postgres。
"""

import uuid
from datetime import datetime, timedelta, timezone

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

SQLALCHEMY_DATABASE_URL = "sqlite:///test_announcements.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

API_PREFIX = "/api/v1"
AUTH_PREFIX = f"{API_PREFIX}/auth"
ANNOUNCEMENTS_URL = f"{API_PREFIX}/announcements"
ADMIN_ANNOUNCEMENTS = f"{API_PREFIX}/admin/announcements"

NOW = datetime.now(timezone.utc)


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
    admin_user = _register_and_login_sync(
        db_session, "admin_test", "admin_test@example.com"
    )
    admin_user.role = "admin"
    db_session.add(admin_user)
    db_session.commit()

    token = await _login(client, "admin_test")
    transport = ASGITransport(app=app)
    return AsyncClient(
        transport=transport,
        base_url="http://test",
        headers={"Authorization": f"Bearer {token}"},
    )


def _make_announcement(**overrides):
    """返回创建公告的 payload 字典。"""
    return {
        "title": "Test Announcement",
        "content": "Announcement content",
        "is_published": True,
        "starts_at": (NOW - timedelta(hours=1)).isoformat(),
        "ends_at": (NOW + timedelta(days=7)).isoformat(),
        **overrides,
    }


# ---------- public list ----------


@pytest.mark.asyncio
async def test_public_list_only_published_in_range(client: AsyncClient, db_session):
    """公开接口只返回已发布且在有效期内的公告。"""
    admin_client = await _get_admin_client(client, db_session)

    # 创建：已过期（不应出现）
    await admin_client.post(
        ADMIN_ANNOUNCEMENTS,
        json=_make_announcement(
            title="Expired",
            starts_at=(NOW - timedelta(days=10)).isoformat(),
            ends_at=(NOW - timedelta(days=1)).isoformat(),
        ),
    )
    # 创建：未发布（不应出现）
    await admin_client.post(
        ADMIN_ANNOUNCEMENTS,
        json=_make_announcement(
            title="Draft",
            is_published=False,
        ),
    )
    # 创建：有效期内（应出现）
    await admin_client.post(
        ADMIN_ANNOUNCEMENTS,
        json=_make_announcement(
            title="Active A",
            starts_at=(NOW - timedelta(hours=2)).isoformat(),
        ),
    )
    await admin_client.post(
        ADMIN_ANNOUNCEMENTS,
        json=_make_announcement(
            title="Active B",
            starts_at=(NOW - timedelta(hours=1)).isoformat(),
        ),
    )

    resp = await client.get(f"{ANNOUNCEMENTS_URL}/")
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()["data"]
    titles = [a["title"] for a in data]
    assert "Active A" in titles
    assert "Active B" in titles
    assert "Expired" not in titles
    assert "Draft" not in titles


@pytest.mark.asyncio
async def test_public_list_ordered_by_starts_at_desc(client: AsyncClient, db_session):
    """公开列表按 starts_at 降序排列。"""
    admin_client = await _get_admin_client(client, db_session)

    await admin_client.post(
        ADMIN_ANNOUNCEMENTS,
        json=_make_announcement(
            title="Older",
            starts_at=(NOW - timedelta(days=2)).isoformat(),
        ),
    )
    await admin_client.post(
        ADMIN_ANNOUNCEMENTS,
        json=_make_announcement(
            title="Newer",
            starts_at=(NOW - timedelta(hours=1)).isoformat(),
        ),
    )

    resp = await client.get(f"{ANNOUNCEMENTS_URL}/")
    data = resp.json()["data"]
    titles = [a["title"] for a in data]
    assert titles[0] == "Newer"


@pytest.mark.asyncio
async def test_public_list_no_start_limit(client: AsyncClient, db_session):
    """starts_at 为空时视为始终有效。"""
    admin_client = await _get_admin_client(client, db_session)

    await admin_client.post(
        ADMIN_ANNOUNCEMENTS,
        json=_make_announcement(
            title="No Start",
            starts_at=None,
        ),
    )

    resp = await client.get(f"{ANNOUNCEMENTS_URL}/")
    data = resp.json()["data"]
    assert any(a["title"] == "No Start" for a in data)


@pytest.mark.asyncio
async def test_public_list_no_end_limit(client: AsyncClient, db_session):
    """ends_at 为空时视为永不过期。"""
    admin_client = await _get_admin_client(client, db_session)

    await admin_client.post(
        ADMIN_ANNOUNCEMENTS,
        json=_make_announcement(
            title="No End",
            ends_at=None,
        ),
    )

    resp = await client.get(f"{ANNOUNCEMENTS_URL}/")
    data = resp.json()["data"]
    assert any(a["title"] == "No End" for a in data)


@pytest.mark.asyncio
async def test_soft_deleted_not_in_public_list(client: AsyncClient, db_session):
    """已软删除的公告不出现在公开列表中。"""
    admin_client = await _get_admin_client(client, db_session)

    resp = await admin_client.post(
        ADMIN_ANNOUNCEMENTS,
        json=_make_announcement(
            title="To Delete",
        ),
    )
    announcement_id = resp.json()["data"]["id"]
    await admin_client.delete(f"{ADMIN_ANNOUNCEMENTS}/{announcement_id}")

    resp = await client.get(f"{ANNOUNCEMENTS_URL}/")
    data = resp.json()["data"]
    assert not any(a["title"] == "To Delete" for a in data)


# ---------- admin CRUD ----------


@pytest.mark.asyncio
async def test_admin_create_announcement(client: AsyncClient, db_session):
    admin_client = await _get_admin_client(client, db_session)

    resp = await admin_client.post(
        ADMIN_ANNOUNCEMENTS, json=_make_announcement(title="New")
    )
    assert resp.status_code == status.HTTP_201_CREATED
    body = resp.json()
    assert body["code"] == 200
    a = body["data"]
    assert a["title"] == "New"
    assert a["is_published"] is True
    assert a["id"]


@pytest.mark.asyncio
async def test_admin_create_requires_admin(client: AsyncClient, db_session):
    _register_and_login_sync(db_session, "normie", "normie@example.com")
    token = await _login(client, "normie")

    resp = await client.post(
        ADMIN_ANNOUNCEMENTS,
        json=_make_announcement(),
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_admin_create_requires_auth(client: AsyncClient):
    resp = await client.post(ADMIN_ANNOUNCEMENTS, json=_make_announcement())
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_admin_edit_announcement(client: AsyncClient, db_session):
    admin_client = await _get_admin_client(client, db_session)

    resp = await admin_client.post(ADMIN_ANNOUNCEMENTS, json=_make_announcement())
    announcement_id = resp.json()["data"]["id"]

    resp = await admin_client.patch(
        f"{ADMIN_ANNOUNCEMENTS}/{announcement_id}",
        json={"title": "Updated", "is_published": False},
    )
    assert resp.status_code == status.HTTP_200_OK
    updated = resp.json()["data"]
    assert updated["title"] == "Updated"
    assert updated["is_published"] is False


@pytest.mark.asyncio
async def test_admin_edit_nonexistent(client: AsyncClient, db_session):
    admin_client = await _get_admin_client(client, db_session)

    resp = await admin_client.patch(
        f"{ADMIN_ANNOUNCEMENTS}/{uuid.uuid4()}",
        json={"title": "Ghost"},
    )
    assert resp.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_admin_delete_announcement(client: AsyncClient, db_session):
    admin_client = await _get_admin_client(client, db_session)

    resp = await admin_client.post(ADMIN_ANNOUNCEMENTS, json=_make_announcement())
    announcement_id = resp.json()["data"]["id"]

    resp = await admin_client.delete(f"{ADMIN_ANNOUNCEMENTS}/{announcement_id}")
    assert resp.status_code == status.HTTP_204_NO_CONTENT

    # 软删除后公开接口不可见
    resp = await client.get(f"{ANNOUNCEMENTS_URL}/")
    data = resp.json()["data"]
    assert not any(a["id"] == announcement_id for a in data)


@pytest.mark.asyncio
async def test_admin_delete_nonexistent(client: AsyncClient, db_session):
    admin_client = await _get_admin_client(client, db_session)

    resp = await admin_client.delete(f"{ADMIN_ANNOUNCEMENTS}/{uuid.uuid4()}")
    assert resp.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_admin_delete_requires_admin(client: AsyncClient, db_session):
    _register_and_login_sync(db_session, "normie2", "normie2@example.com")
    token = await _login(client, "normie2")

    resp = await client.delete(
        f"{ADMIN_ANNOUNCEMENTS}/{uuid.uuid4()}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_admin_list_all_includes_unpublished(client: AsyncClient, db_session):
    """管理端列表应包含未发布的公告。"""
    admin_client = await _get_admin_client(client, db_session)

    await admin_client.post(
        ADMIN_ANNOUNCEMENTS,
        json=_make_announcement(
            title="Published One",
        ),
    )
    await admin_client.post(
        ADMIN_ANNOUNCEMENTS,
        json=_make_announcement(
            title="Draft One",
            is_published=False,
        ),
    )

    resp = await admin_client.get(ADMIN_ANNOUNCEMENTS)
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()["data"]
    titles = [a["title"] for a in data]
    assert "Published One" in titles
    assert "Draft One" in titles


@pytest.mark.asyncio
async def test_admin_list_requires_admin(client: AsyncClient, db_session):
    _register_and_login_sync(db_session, "normie3", "normie3@example.com")
    token = await _login(client, "normie3")

    resp = await client.get(
        ADMIN_ANNOUNCEMENTS,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == status.HTTP_403_FORBIDDEN
