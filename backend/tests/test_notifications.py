"""
Notifications 路由集成测试：列表、未读计数、单条已读、全部已读。
"""

from datetime import datetime
from datetime import timedelta
from datetime import timezone
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
from app.models.notification import Notification
from app.services.email_service import EmailService

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


def _override_get_email_service():
    return _make_mock_email_service()


@pytest.fixture()
def client():
    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_email_service] = _override_get_email_service
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
API_PREFIX = "/api/v1/notifications"


def _register_and_login(
    client, db_session, username="notifyuser", email="notify@example.com"
) -> tuple[str, str]:
    client.post(
        f"{AUTH_PREFIX}/register",
        json={
            "username": username,
            "email": email,
            "password": "securepass123",
        },
    )

    from app.models.user import User

    user = db_session.query(User).filter(User.username == username).first()
    user.email_verified = True
    db_session.add(user)
    db_session.commit()

    login_resp = client.post(
        f"{AUTH_PREFIX}/login",
        json={"account": username, "password": "securepass123"},
    )
    data = login_resp.json()["data"]
    return data["access_token"], data["user"]["id"]


def _create_notification(
    db_session,
    *,
    recipient_id: str,
    actor_id: str | None = None,
    type: str = "comment",
    title: str = "New activity",
    content: str = "Someone interacted with your post",
    is_read: bool = False,
    created_at: datetime | None = None,
) -> Notification:
    read_at = datetime.now(timezone.utc) if is_read else None
    notification = Notification(
        recipient_id=UUID(recipient_id),
        actor_id=UUID(actor_id) if actor_id else None,
        type=type,
        title=title,
        content=content,
        related_type="post",
        related_id=None,
        is_read=is_read,
        read_at=read_at,
    )
    if created_at is not None:
        notification.created_at = created_at
    db_session.add(notification)
    db_session.commit()
    db_session.refresh(notification)
    return notification


def test_list_notifications_requires_auth(client):
    resp = client.get(API_PREFIX)

    assert resp.status_code == 401


def test_list_notifications_returns_current_user_notifications_unread_first(
    client, db_session
):
    token, user_id = _register_and_login(client, db_session)
    _, other_id = _register_and_login(
        client, db_session, username="othernotify", email="othernotify@example.com"
    )
    now = datetime.now(timezone.utc)
    unread = _create_notification(
        db_session,
        recipient_id=user_id,
        title="Unread",
        is_read=False,
        created_at=now - timedelta(days=1),
    )
    read = _create_notification(
        db_session,
        recipient_id=user_id,
        title="Read",
        is_read=True,
        created_at=now,
    )
    _create_notification(db_session, recipient_id=other_id, title="Other user")

    resp = client.get(
        API_PREFIX,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 200
    body = resp.json()["data"]
    assert body["pagination"]["total"] == 2
    assert [item["id"] for item in body["items"]] == [str(unread.id), str(read.id)]
    assert [item["is_read"] for item in body["items"]] == [False, True]


def test_unread_count_only_counts_current_user_unread(client, db_session):
    token, user_id = _register_and_login(client, db_session)
    _, other_id = _register_and_login(
        client, db_session, username="countother", email="countother@example.com"
    )
    _create_notification(db_session, recipient_id=user_id)
    _create_notification(db_session, recipient_id=user_id, is_read=True)
    _create_notification(db_session, recipient_id=other_id)

    resp = client.get(
        f"{API_PREFIX}/unread-count",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 200
    assert resp.json()["data"]["unread_count"] == 1


def test_mark_notification_as_read(client, db_session):
    token, user_id = _register_and_login(client, db_session)
    notification = _create_notification(db_session, recipient_id=user_id)

    resp = client.put(
        f"{API_PREFIX}/{notification.id}/read",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["id"] == str(notification.id)
    assert data["is_read"] is True
    assert data["read_at"] is not None


def test_cannot_mark_other_users_notification(client, db_session):
    token, _ = _register_and_login(client, db_session)
    _, other_id = _register_and_login(
        client, db_session, username="markother", email="markother@example.com"
    )
    notification = _create_notification(db_session, recipient_id=other_id)

    resp = client.put(
        f"{API_PREFIX}/{notification.id}/read",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 404


def test_mark_all_notifications_as_read(client, db_session):
    token, user_id = _register_and_login(client, db_session)
    _, other_id = _register_and_login(
        client, db_session, username="allother", email="allother@example.com"
    )
    _create_notification(db_session, recipient_id=user_id)
    _create_notification(db_session, recipient_id=user_id)
    _create_notification(db_session, recipient_id=user_id, is_read=True)
    _create_notification(db_session, recipient_id=other_id)

    resp = client.put(
        f"{API_PREFIX}/read-all",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["updated_count"] == 2
    assert data["unread_count"] == 0
