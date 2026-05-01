"""
Users 路由集成测试：profile / public profile / admin 用户管理

覆盖正常/异常场景、响应格式校验、权限控制。
复用 test_auth.py 的 SQLite + TestClient 模式。
"""

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import get_db
from app.main import app
from app.models.base import Base

# ---------- 测试数据库 fixtures ----------

SQLALCHEMY_DATABASE_URL = "sqlite:///test.db"

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


@pytest.fixture()
def client():
    app.dependency_overrides[get_db] = _override_get_db
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


# ---------- helpers ----------

AUTH_PREFIX = "/api/v1/auth"
API_PREFIX = "/api/v1/users"


def _register_and_login(
    client, username="testuser", email="test@example.com"
) -> tuple[str, str]:
    """注册用户并登录，返回 (token, user_id)。"""
    client.post(
        f"{AUTH_PREFIX}/register",
        json={
            "username": username,
            "email": email,
            "password": "securepass123",
        },
    )
    login_resp = client.post(
        f"{AUTH_PREFIX}/login",
        json={"account": username, "password": "securepass123"},
    )
    data = login_resp.json()["data"]
    return data["access_token"], data["user"]["id"]


def _register_and_login_admin(
    client, db_session, username="adminuser", email="admin@example.com"
) -> tuple[str, str]:
    """注册用户并通过 DB 提权为 admin，返回 (token, user_id)。"""
    token, user_id = _register_and_login(client, username, email)
    from uuid import UUID

    from app.models.user import User

    user = db_session.query(User).filter(User.id == UUID(user_id)).first()
    user.role = "admin"
    db_session.add(user)
    db_session.commit()
    return token, user_id


# ---------- GET /users/me ----------


class TestGetCurrentUserProfile:
    def test_success(self, client):
        token, user_id = _register_and_login(client)

        resp = client.get(
            f"{API_PREFIX}/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 200
        assert body["message"] == "success"
        data = body["data"]
        assert data["id"] == user_id
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
        assert data["role"] == "user"
        assert data["status"] == "active"
        assert "created_at" in data
        assert "updated_at" in data

    def test_requires_auth(self, client):
        resp = client.get(f"{API_PREFIX}/me")
        assert resp.status_code == 401

    def test_revoked_token(self, client):
        token, _ = _register_and_login(client, "revokeme", "revoke@example.com")
        client.post(
            f"{AUTH_PREFIX}/logout",
            headers={"Authorization": f"Bearer {token}"},
        )
        resp = client.get(
            f"{API_PREFIX}/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 401
        assert "revoked" in resp.json()["detail"]


# ---------- PATCH /users/me ----------


class TestUpdateCurrentUserProfile:
    def test_update_nickname(self, client):
        token, _ = _register_and_login(client)

        resp = client.patch(
            f"{API_PREFIX}/me",
            json={"nickname": "NewNick"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["nickname"] == "NewNick"

    def test_update_avatar_url(self, client):
        token, _ = _register_and_login(client)

        resp = client.patch(
            f"{API_PREFIX}/me",
            json={"avatar_url": "https://example.com/avatar.png"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["avatar_url"] == "https://example.com/avatar.png"

    def test_update_both_fields(self, client):
        token, _ = _register_and_login(client)

        resp = client.patch(
            f"{API_PREFIX}/me",
            json={
                "nickname": "CoolNick",
                "avatar_url": "https://example.com/pic.png",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["nickname"] == "CoolNick"
        assert data["avatar_url"] == "https://example.com/pic.png"

    def test_requires_auth(self, client):
        resp = client.patch(
            f"{API_PREFIX}/me",
            json={"nickname": "NoAuth"},
        )
        assert resp.status_code == 401


# ---------- GET /users/{id} ----------


class TestGetUserPublicProfile:
    def test_success(self, client):
        _, user_id = _register_and_login(client)

        resp = client.get(f"{API_PREFIX}/{user_id}")
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 200
        data = body["data"]
        assert data["id"] == user_id
        assert data["username"] == "testuser"
        assert data["role"] == "user"
        assert "email" not in data
        assert "created_at" not in data

    def test_user_not_found(self, client):
        random_id = str(uuid.uuid4())
        resp = client.get(f"{API_PREFIX}/{random_id}")
        assert resp.status_code == 404
        assert "User not found" in resp.json()["detail"]

    def test_invalid_uuid_returns_404(self, client):
        resp = client.get(f"{API_PREFIX}/not-a-valid-uuid")
        assert resp.status_code == 404


# ---------- GET /users/ (admin list) ----------


class TestListUsers:
    def test_empty_list(self, client, db_session):
        token, _ = _register_and_login_admin(client, db_session)

        resp = client.get(
            f"{API_PREFIX}/",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 200
        assert body["message"] == "success"
        data = body["data"]
        assert isinstance(data["items"], list)
        assert data["pagination"]["page"] == 1
        assert data["pagination"]["page_size"] == 20
        assert data["pagination"]["total"] >= 0
        assert "total_pages" in data["pagination"]

    def test_with_users(self, client, db_session):
        token, _ = _register_and_login_admin(
            client, db_session, "admin1", "admin1@e.com"
        )
        _register_and_login(client, "user_a", "a@example.com")
        _register_and_login(client, "user_b", "b@example.com")

        resp = client.get(
            f"{API_PREFIX}/",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        items = resp.json()["data"]["items"]
        assert len(items) >= 2
        for item in items:
            assert "id" in item
            assert "username" in item
            assert "email" in item
            assert "role" in item
            assert "status" in item
            assert "created_at" in item

    def test_pagination(self, client, db_session):
        token, _ = _register_and_login_admin(
            client, db_session, "admin2", "admin2@e.com"
        )
        for i in range(5):
            _register_and_login(client, f"pageuser_{i}", f"page{i}@example.com")

        resp = client.get(
            f"{API_PREFIX}/",
            params={"page": 1, "page_size": 3},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        pagination = resp.json()["data"]["pagination"]
        assert pagination["page"] == 1
        assert pagination["page_size"] == 3
        assert len(resp.json()["data"]["items"]) <= 3

    def test_forbidden_for_normal_user(self, client):
        token, _ = _register_and_login(client, "normalguy", "normal@example.com")

        resp = client.get(
            f"{API_PREFIX}/",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403
        assert "Admin required" in resp.json()["detail"]

    def test_requires_auth(self, client):
        resp = client.get(f"{API_PREFIX}/")
        assert resp.status_code == 401


# ---------- PATCH /users/{id}/status ----------


class TestUpdateUserStatus:
    def test_ban_user(self, client, db_session):
        admin_token, _ = _register_and_login_admin(
            client, db_session, "admin3", "admin3@e.com"
        )
        _, target_id = _register_and_login(client, "victim", "victim@example.com")

        resp = client.patch(
            f"{API_PREFIX}/{target_id}/status",
            json={"status": "banned"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["id"] == target_id
        assert data["status"] == "banned"

    def test_activate_user(self, client, db_session):
        admin_token, _ = _register_and_login_admin(
            client, db_session, "admin4", "admin4@e.com"
        )
        _, target_id = _register_and_login(client, "inactiveu", "inactive@example.com")

        client.patch(
            f"{API_PREFIX}/{target_id}/status",
            json={"status": "banned"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        resp = client.patch(
            f"{API_PREFIX}/{target_id}/status",
            json={"status": "active"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["status"] == "active"

    def test_user_not_found(self, client, db_session):
        token, _ = _register_and_login_admin(
            client, db_session, "admin5", "admin5@e.com"
        )
        random_id = str(uuid.uuid4())

        resp = client.patch(
            f"{API_PREFIX}/{random_id}/status",
            json={"status": "banned"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404

    def test_invalid_status_value(self, client, db_session):
        token, _ = _register_and_login_admin(
            client, db_session, "admin6", "admin6@e.com"
        )
        _, target_id = _register_and_login(client, "target2", "target2@example.com")

        resp = client.patch(
            f"{API_PREFIX}/{target_id}/status",
            json={"status": "deleted"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 422

    def test_forbidden_for_normal_user(self, client):
        token, _ = _register_and_login(client, "normie", "normie@example.com")
        _, target_id = _register_and_login(client, "target3", "target3@example.com")

        resp = client.patch(
            f"{API_PREFIX}/{target_id}/status",
            json={"status": "banned"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403

    def test_requires_auth(self, client):
        resp = client.patch(
            f"{API_PREFIX}/{str(uuid.uuid4())}/status",
            json={"status": "banned"},
        )
        assert resp.status_code == 401
