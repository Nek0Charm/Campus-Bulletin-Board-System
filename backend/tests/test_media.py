"""
Media 路由集成测试：上传/代理下载/元数据/删除/附件/头像

使用 TestClient + 内存 SQLite + InMemoryStorageBackend 替代真实 Postgres 和 S3。
"""

import uuid
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import get_db
from app.deps import get_email_service
from app.deps.services import get_media_service
from app.main import app
from app.models.base import Base
from app.models.board import Board
from app.models.user import User
from app.services.email_service import EmailService
from app.services.media_service import MediaService
from app.storage.memory import InMemoryStorageBackend
from app.utils.security import hash_password

SQLALCHEMY_DATABASE_URL = "sqlite:///test_media.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

API_PREFIX = "/api/v1"
MEDIA_URL = f"{API_PREFIX}/media"
USERS_URL = f"{API_PREFIX}/users"
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


_in_memory_storage = InMemoryStorageBackend()
_media_service = MediaService(storage=_in_memory_storage)


def _override_get_media_service():
    return _media_service


def _make_mock_email_service() -> EmailService:
    svc = EmailService()
    svc.send_verification_email = Mock()
    import app.services.email_service as mod

    svc.generate_verify_token = mod.EmailService.generate_verify_token.__get__(
        svc, EmailService
    )
    svc.decode_verify_token = mod.EmailService.decode_verify_token.__get__(
        svc, EmailService
    )
    return svc


def _override_get_email_service():
    return _make_mock_email_service()


@pytest.fixture()
def client():
    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_media_service] = _override_get_media_service
    app.dependency_overrides[get_email_service] = _override_get_email_service
    _in_memory_storage._store.clear()
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


def _create_user(db, username: str = "testuser", role: str = "user") -> User:
    user = User(
        username=username,
        email=f"{username}@test.com",
        password_hash=hash_password("securepass123"),
        nickname=username,
        role=role,
        status="active",
        email_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _create_board(db, name: str = "Test Board", slug: str = "test-board") -> Board:
    board = Board(name=name, slug=slug, description="test", sort_order=1)
    db.add(board)
    db.commit()
    db.refresh(board)
    return board


def _login(client: TestClient, account: str) -> str:
    resp = client.post(
        f"{AUTH_PREFIX}/login",
        json={"account": account, "password": "securepass123"},
    )
    return resp.json()["data"]["access_token"]


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


SMALL_PNG = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"


def _upload_png(client: TestClient, token: str, source_type: str = "post") -> dict:
    resp = client.post(
        f"{MEDIA_URL}/upload?source_type={source_type}",
        headers=_auth_headers(token),
        files={"file": ("test.png", SMALL_PNG, "image/png")},
    )
    assert resp.status_code == 201, f"Upload failed: {resp.text}"
    return resp.json()["data"]


# =============================== 上传 ===============================


def test_upload_image_success(client: TestClient, db_session):
    _create_user(db_session)
    token = _login(client, "testuser")
    data = _upload_png(client, token)
    assert "id" in data
    assert data["url"].startswith("/api/v1/media/")
    assert data["file_name"] == "test.png"
    assert data["mime_type"] == "image/png"
    assert data["file_size"] > 0


def test_upload_image_invalid_mime(client: TestClient, db_session):
    _create_user(db_session)
    token = _login(client, "testuser")
    resp = client.post(
        f"{MEDIA_URL}/upload?source_type=post",
        headers=_auth_headers(token),
        files={"file": ("test.txt", b"hello", "text/plain")},
    )
    assert resp.status_code == 400


def test_upload_image_requires_auth(client: TestClient, db_session):
    resp = client.post(
        f"{MEDIA_URL}/upload?source_type=post",
        files={"file": ("test.png", SMALL_PNG, "image/png")},
    )
    assert resp.status_code == 401


def test_upload_image_valid_source_types(client: TestClient, db_session):
    _create_user(db_session)
    token = _login(client, "testuser")
    for source_type in ("post", "comment", "avatar"):
        resp = client.post(
            f"{MEDIA_URL}/upload?source_type={source_type}",
            headers=_auth_headers(token),
            files={"file": (f"test_{source_type}.png", SMALL_PNG, "image/png")},
        )
        assert resp.status_code == 201, f"source_type={source_type} failed"
        assert "data" in resp.json()


def test_upload_image_invalid_source_type(client: TestClient, db_session):
    _create_user(db_session)
    token = _login(client, "testuser")
    resp = client.post(
        f"{MEDIA_URL}/upload?source_type=invalid",
        headers=_auth_headers(token),
        files={"file": ("test.png", SMALL_PNG, "image/png")},
    )
    assert resp.status_code == 400


def test_upload_image_dedup_same_user(client: TestClient, db_session):
    _create_user(db_session)
    token = _login(client, "testuser")
    data1 = _upload_png(client, token)
    data2 = _upload_png(client, token)
    assert data1["id"] == data2["id"]


def test_upload_image_different_user_no_dedup(client: TestClient, db_session):
    _create_user(db_session, "user_a")
    _create_user(db_session, "user_b")
    token_a = _login(client, "user_a")
    token_b = _login(client, "user_b")
    data_a = _upload_png(client, token_a)
    data_b = _upload_png(client, token_b)
    assert data_a["id"] != data_b["id"]


# =============================== 代理下载 ===============================


def test_get_media_success(client: TestClient, db_session):
    _create_user(db_session)
    token = _login(client, "testuser")
    data = _upload_png(client, token)
    media_id = data["id"]
    resp = client.get(f"{MEDIA_URL}/{media_id}")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "image/png"
    assert resp.content == SMALL_PNG


def test_get_media_not_found(client: TestClient, db_session):
    resp = client.get(f"{MEDIA_URL}/{uuid.uuid4()}")
    assert resp.status_code == 404


# =============================== 元数据 ===============================


def test_get_media_info_success(client: TestClient, db_session):
    _create_user(db_session)
    token = _login(client, "testuser")
    upload_data = _upload_png(client, token)
    media_id = upload_data["id"]
    resp = client.get(f"{MEDIA_URL}/{media_id}/info", headers=_auth_headers(token))
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["id"] == media_id
    assert data["file_name"] == "test.png"
    assert data["mime_type"] == "image/png"
    assert data["source_type"] == "post"


def test_get_media_info_requires_auth(client: TestClient, db_session):
    resp = client.get(f"{MEDIA_URL}/{uuid.uuid4()}/info")
    assert resp.status_code == 401


# =============================== 删除 ===============================


def test_delete_media_by_uploader(client: TestClient, db_session):
    _create_user(db_session)
    token = _login(client, "testuser")
    data = _upload_png(client, token)
    media_id = data["id"]
    resp = client.delete(f"{MEDIA_URL}/{media_id}", headers=_auth_headers(token))
    assert resp.status_code == 200
    assert resp.json()["message"] == "Media deleted"


def test_delete_media_by_admin(client: TestClient, db_session):
    _create_user(db_session, "normal_user")
    _create_user(db_session, "admin_user", role="admin")
    token_normal = _login(client, "normal_user")
    token_admin = _login(client, "admin_user")
    data = _upload_png(client, token_normal)
    media_id = data["id"]
    resp = client.delete(f"{MEDIA_URL}/{media_id}", headers=_auth_headers(token_admin))
    assert resp.status_code == 200
    assert resp.json()["message"] == "Media deleted"


def test_delete_media_by_other_user_403(client: TestClient, db_session):
    _create_user(db_session, "owner")
    _create_user(db_session, "other")
    token_owner = _login(client, "owner")
    token_other = _login(client, "other")
    data = _upload_png(client, token_owner)
    media_id = data["id"]
    resp = client.delete(f"{MEDIA_URL}/{media_id}", headers=_auth_headers(token_other))
    assert resp.status_code == 403


def test_delete_media_not_found(client: TestClient, db_session):
    _create_user(db_session)
    token = _login(client, "testuser")
    resp = client.delete(f"{MEDIA_URL}/{uuid.uuid4()}", headers=_auth_headers(token))
    assert resp.status_code == 404


# =============================== 附件 ===============================


def test_attach_to_post_success(client: TestClient, db_session):
    _create_user(db_session)
    board = _create_board(db_session)
    token = _login(client, "testuser")
    headers = _auth_headers(token)
    data = _upload_png(client, token)
    media_id = data["id"]
    post_resp = client.post(
        f"{API_PREFIX}/posts/",
        headers=headers,
        json={"title": "Test Post", "content": "Hello", "board_id": str(board.id)},
    )
    post_id = post_resp.json()["data"]["id"]
    attach_resp = client.post(
        f"{MEDIA_URL}/posts/{post_id}/attachments",
        headers=headers,
        json={"media_ids": [media_id]},
    )
    assert attach_resp.status_code == 201
    result = attach_resp.json()["data"]
    assert len(result) == 1
    assert result[0]["media_id"] == media_id


def test_attach_to_post_media_not_found(client: TestClient, db_session):
    _create_user(db_session)
    board = _create_board(db_session)
    token = _login(client, "testuser")
    headers = _auth_headers(token)
    post_resp = client.post(
        f"{API_PREFIX}/posts/",
        headers=headers,
        json={"title": "Test Post", "content": "Hello", "board_id": str(board.id)},
    )
    post_id = post_resp.json()["data"]["id"]
    attach_resp = client.post(
        f"{MEDIA_URL}/posts/{post_id}/attachments",
        headers=headers,
        json={"media_ids": [str(uuid.uuid4())]},
    )
    assert attach_resp.status_code == 404


# =============================== 头像 ===============================


def test_upload_avatar_success(client: TestClient, db_session):
    _create_user(db_session)
    token = _login(client, "testuser")
    headers = _auth_headers(token)
    resp = client.patch(
        f"{USERS_URL}/me/avatar",
        headers=headers,
        files={"file": ("avatar.png", SMALL_PNG, "image/png")},
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "avatar_url" in data
    assert data["avatar_url"].startswith("/api/v1/media/")


def test_upload_avatar_requires_auth(client: TestClient, db_session):
    resp = client.patch(
        f"{USERS_URL}/me/avatar",
        files={"file": ("avatar.png", SMALL_PNG, "image/png")},
    )
    assert resp.status_code == 401


def test_upload_avatar_invalid_mime(client: TestClient, db_session):
    _create_user(db_session)
    token = _login(client, "testuser")
    headers = _auth_headers(token)
    resp = client.patch(
        f"{USERS_URL}/me/avatar",
        headers=headers,
        files={"file": ("avatar.txt", b"not an image", "text/plain")},
    )
    assert resp.status_code == 400
