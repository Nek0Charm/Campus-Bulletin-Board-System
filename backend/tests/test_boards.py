"""
Boards 路由集成测试：公开查询、admin 管理、软删除。
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import get_db
from app.main import app
from app.models.base import Base

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


AUTH_PREFIX = "/api/v1/auth"
API_PREFIX = "/api/v1/boards"


def _register_and_login(
    client, username="boarduser", email="boarduser@example.com"
) -> tuple[str, str]:
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
    client, db_session, username="boardadmin", email="boardadmin@example.com"
) -> tuple[str, str]:
    token, user_id = _register_and_login(client, username, email)

    from uuid import UUID

    from app.models.user import User

    user = db_session.query(User).filter(User.id == UUID(user_id)).first()
    user.role = "admin"
    db_session.add(user)
    db_session.commit()
    return token, user_id


def _create_board(client, token, name="General", slug="general", sort_order=10):
    return client.post(
        API_PREFIX,
        json={
            "name": name,
            "slug": slug,
            "description": f"{name} board",
            "sort_order": sort_order,
        },
        headers={"Authorization": f"Bearer {token}"},
    )


def test_list_boards_orders_by_sort_order(client, db_session):
    token, _ = _register_and_login_admin(client, db_session)
    _create_board(client, token, name="Later", slug="later", sort_order=20)
    _create_board(client, token, name="First", slug="first", sort_order=1)
    _create_board(client, token, name="Middle", slug="middle", sort_order=10)

    resp = client.get(API_PREFIX)

    assert resp.status_code == 200
    items = resp.json()["data"]
    assert [item["slug"] for item in items] == ["first", "middle", "later"]


def test_get_board_detail(client, db_session):
    token, _ = _register_and_login_admin(client, db_session)
    create_resp = _create_board(client, token)
    board_id = create_resp.json()["data"]["id"]

    resp = client.get(f"{API_PREFIX}/{board_id}")

    assert resp.status_code == 200
    assert resp.json()["data"]["id"] == board_id
    assert resp.json()["data"]["slug"] == "general"


def test_non_admin_cannot_create_update_or_delete_board(client, db_session):
    admin_token, _ = _register_and_login_admin(client, db_session)
    user_token, _ = _register_and_login(
        client, username="normaluser", email="normal@example.com"
    )
    board_id = _create_board(client, admin_token).json()["data"]["id"]
    headers = {"Authorization": f"Bearer {user_token}"}

    create_resp = client.post(
        API_PREFIX,
        json={"name": "User Board", "slug": "user-board", "sort_order": 1},
        headers=headers,
    )
    update_resp = client.patch(
        f"{API_PREFIX}/{board_id}",
        json={"name": "Blocked"},
        headers=headers,
    )
    delete_resp = client.delete(f"{API_PREFIX}/{board_id}", headers=headers)

    assert create_resp.status_code == 403
    assert update_resp.status_code == 403
    assert delete_resp.status_code == 403


def test_admin_can_update_board(client, db_session):
    token, _ = _register_and_login_admin(client, db_session)
    board_id = _create_board(client, token).json()["data"]["id"]

    resp = client.patch(
        f"{API_PREFIX}/{board_id}",
        json={"name": "Campus Life", "sort_order": 2},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["name"] == "Campus Life"
    assert data["sort_order"] == 2


def test_deleted_board_is_hidden_from_list(client, db_session):
    token, _ = _register_and_login_admin(client, db_session)
    board_id = _create_board(client, token).json()["data"]["id"]

    delete_resp = client.delete(
        f"{API_PREFIX}/{board_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    list_resp = client.get(API_PREFIX)
    detail_resp = client.get(f"{API_PREFIX}/{board_id}")

    assert delete_resp.status_code == 200
    assert list_resp.status_code == 200
    assert list_resp.json()["data"] == []
    assert detail_resp.status_code == 404
