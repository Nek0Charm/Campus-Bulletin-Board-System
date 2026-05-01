"""
Auth 路由集成测试：register / login / logout

使用 TestClient + 内存 SQLite 替代真实 Postgres，避免外部依赖。
通过 override_deps 注入测试数据库 session 和 auth service。
"""

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
    """每个测试前后创建/清理表，保证隔离。"""
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
    """注入测试 DB session 的 TestClient。"""
    app.dependency_overrides[get_db] = _override_get_db
    c = TestClient(app)
    yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def db_session():
    """直接暴露测试 Session，供需要 db 操作的测试用。"""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------- register 测试 ----------

API_PREFIX = "/api/v1/auth"


def test_register_success(client):
    resp = client.post(
        f"{API_PREFIX}/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "securepass123",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 200
    assert body["data"]["user"]["username"] == "testuser"
    assert body["data"]["user"]["email"] == "test@example.com"
    assert body["data"]["user"]["role"] == "user"
    assert body["data"]["user"]["status"] == "active"
    assert "id" in body["data"]["user"]


def test_register_with_nickname(client):
    resp = client.post(
        f"{API_PREFIX}/register",
        json={
            "username": "nickuser",
            "email": "nick@example.com",
            "password": "securepass123",
            "nickname": "CoolNick",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["user"]["nickname"] == "CoolNick"


def test_register_duplicate_username(client):
    client.post(
        f"{API_PREFIX}/register",
        json={
            "username": "dupuser",
            "email": "first@example.com",
            "password": "securepass123",
        },
    )
    resp = client.post(
        f"{API_PREFIX}/register",
        json={
            "username": "dupuser",
            "email": "second@example.com",
            "password": "securepass123",
        },
    )
    assert resp.status_code == 409
    assert "Username already exists" in resp.json()["detail"]


def test_register_duplicate_email(client):
    client.post(
        f"{API_PREFIX}/register",
        json={
            "username": "user1",
            "email": "same@example.com",
            "password": "securepass123",
        },
    )
    resp = client.post(
        f"{API_PREFIX}/register",
        json={
            "username": "user2",
            "email": "same@example.com",
            "password": "securepass123",
        },
    )
    assert resp.status_code == 409
    assert "Email already exists" in resp.json()["detail"]


def test_register_invalid_short_password(client):
    resp = client.post(
        f"{API_PREFIX}/register",
        json={
            "username": "shortpw",
            "email": "shortpw@example.com",
            "password": "1234567",
        },
    )
    assert resp.status_code == 422


def test_register_invalid_email(client):
    resp = client.post(
        f"{API_PREFIX}/register",
        json={
            "username": "bademail",
            "email": "not-an-email",
            "password": "securepass123",
        },
    )
    assert resp.status_code == 422


def test_register_short_username(client):
    resp = client.post(
        f"{API_PREFIX}/register",
        json={
            "username": "ab",
            "email": "short@example.com",
            "password": "securepass123",
        },
    )
    assert resp.status_code == 422


# ---------- login 测试 ----------


def _register_user(client, username="logintest", email="login@example.com"):
    client.post(
        f"{API_PREFIX}/register",
        json={
            "username": username,
            "email": email,
            "password": "securepass123",
        },
    )


def test_login_with_username(client):
    _register_user(client)
    resp = client.post(
        f"{API_PREFIX}/login",
        json={"account": "logintest", "password": "securepass123"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["data"]["access_token"]
    assert body["data"]["token_type"] == "bearer"
    assert body["data"]["expires_in"] == 3600
    assert body["data"]["user"]["username"] == "logintest"


def test_login_with_email(client):
    _register_user(client)
    resp = client.post(
        f"{API_PREFIX}/login",
        json={"account": "login@example.com", "password": "securepass123"},
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["access_token"]


def test_login_wrong_password(client):
    _register_user(client)
    resp = client.post(
        f"{API_PREFIX}/login",
        json={"account": "logintest", "password": "wrongpassword1"},
    )
    assert resp.status_code == 401
    assert "Invalid account or password" in resp.json()["detail"]


def test_login_nonexistent_user(client):
    resp = client.post(
        f"{API_PREFIX}/login",
        json={"account": "ghost", "password": "securepass123"},
    )
    assert resp.status_code == 401


def test_login_banned_user(client, db_session):
    _register_user(client)
    from app.models.user import User

    user = db_session.query(User).filter(User.username == "logintest").first()
    user.status = "banned"
    db_session.add(user)
    db_session.commit()

    resp = client.post(
        f"{API_PREFIX}/login",
        json={"account": "logintest", "password": "securepass123"},
    )
    assert resp.status_code == 403
    assert "banned" in resp.json()["detail"]


def test_login_inactive_user(client, db_session):
    _register_user(client)
    from app.models.user import User

    user = db_session.query(User).filter(User.username == "logintest").first()
    user.status = "inactive"
    db_session.add(user)
    db_session.commit()

    resp = client.post(
        f"{API_PREFIX}/login",
        json={"account": "logintest", "password": "securepass123"},
    )
    assert resp.status_code == 403


def test_login_updates_last_login_at(client, db_session):
    _register_user(client)
    from app.models.user import User

    user_before = db_session.query(User).filter(User.username == "logintest").first()
    assert user_before.last_login_at is None

    client.post(
        f"{API_PREFIX}/login",
        json={"account": "logintest", "password": "securepass123"},
    )

    db_session.expire_all()
    user_after = db_session.query(User).filter(User.username == "logintest").first()
    assert user_after.last_login_at is not None


# ---------- logout 测试 ----------


def test_logout(client):
    _register_user(client, "logoutuser", "logout@example.com")
    login_resp = client.post(
        f"{API_PREFIX}/login",
        json={"account": "logoutuser", "password": "securepass123"},
    )
    token = login_resp.json()["data"]["access_token"]

    resp = client.post(
        f"{API_PREFIX}/logout",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["message"] == "logout success"


def test_logout_blacklists_token(client):
    _register_user(client, "bluser", "bl@example.com")
    login_resp = client.post(
        f"{API_PREFIX}/login",
        json={"account": "bluser", "password": "securepass123"},
    )
    token = login_resp.json()["data"]["access_token"]

    client.post(
        f"{API_PREFIX}/logout",
        headers={"Authorization": f"Bearer {token}"},
    )

    resp = client.post(
        f"{API_PREFIX}/reset-password",
        json={"old_password": "securepass123", "new_password": "newpass12345"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 401
    assert "revoked" in resp.json()["detail"]


def test_logout_requires_auth(client):
    resp = client.post(f"{API_PREFIX}/logout")
    assert resp.status_code == 401


# ---------- reset-password 测试 ----------


def test_reset_password_success(client):
    _register_user(client, "resetuser", "reset@example.com")
    login_resp = client.post(
        f"{API_PREFIX}/login",
        json={"account": "resetuser", "password": "securepass123"},
    )
    token = login_resp.json()["data"]["access_token"]

    resp = client.post(
        f"{API_PREFIX}/reset-password",
        json={"old_password": "securepass123", "new_password": "newpass12345"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["message"] == "password reset success"

    resp = client.post(
        f"{API_PREFIX}/login",
        json={"account": "resetuser", "password": "securepass123"},
    )
    assert resp.status_code == 401

    resp = client.post(
        f"{API_PREFIX}/login",
        json={"account": "resetuser", "password": "newpass12345"},
    )
    assert resp.status_code == 200


def test_reset_password_wrong_old_password(client):
    _register_user(client, "wrongold", "wrongold@example.com")
    login_resp = client.post(
        f"{API_PREFIX}/login",
        json={"account": "wrongold", "password": "securepass123"},
    )
    token = login_resp.json()["data"]["access_token"]

    resp = client.post(
        f"{API_PREFIX}/reset-password",
        json={"old_password": "wrongpassword1", "new_password": "newpass12345"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 401
    assert "incorrect" in resp.json()["detail"].lower()


def test_reset_password_short_new_password(client):
    _register_user(client, "shortnew", "shortnew@example.com")
    login_resp = client.post(
        f"{API_PREFIX}/login",
        json={"account": "shortnew", "password": "securepass123"},
    )
    token = login_resp.json()["data"]["access_token"]

    resp = client.post(
        f"{API_PREFIX}/reset-password",
        json={"old_password": "securepass123", "new_password": "1234567"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 422


def test_reset_password_requires_auth(client):
    resp = client.post(
        f"{API_PREFIX}/reset-password",
        json={"old_password": "securepass123", "new_password": "newpass12345"},
    )
    assert resp.status_code == 401
