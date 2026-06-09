from uuid import UUID
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import get_db
from app.deps.auth import create_access_token
from app.main import app
from app.models.base import Base
from app.models.board import Board
from app.models.moderation_log import ModerationLog
from app.models.post import Post
from app.models.report import Report
from app.models.user import User

SQLALCHEMY_DATABASE_URL = "sqlite://"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
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


@pytest.fixture
def client():
    app.dependency_overrides[get_db] = _override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def _auth_headers(user: User) -> dict[str, str]:
    token = create_access_token(str(user.id), user.role)
    return {"Authorization": f"Bearer {token}"}


def _create_user(db, *, username: str = "user", role: str = "user") -> User:
    user = User(
        username=username,
        email=f"{username}@example.com",
        password_hash="hashed-password",
        role=role,
        status="active",
        email_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _create_board(db) -> Board:
    board = Board(name="General", slug="general", description="General board")
    db.add(board)
    db.commit()
    db.refresh(board)
    return board


def _create_post(db, *, author: User, board: Board) -> Post:
    post = Post(title="Hello", content="World", author_id=author.id, board_id=board.id)
    db.add(post)
    db.commit()
    db.refresh(post)
    return post


def test_user_can_create_post_report(client, db_session):
    user = _create_user(db_session)
    board = _create_board(db_session)
    post = _create_post(db_session, author=user, board=board)

    response = client.post(
        "/api/v1/reports/",
        json={"target_type": "post", "target_id": str(post.id), "reason": "spam"},
        headers=_auth_headers(user),
    )

    assert response.status_code == 201
    data = response.json()["data"]
    assert data["reporter_id"] == str(user.id)
    assert data["target_type"] == "post"
    assert data["target_id"] == str(post.id)
    assert data["status"] == "pending"


def test_report_missing_target_returns_404(client, db_session):
    user = _create_user(db_session)

    response = client.post(
        "/api/v1/reports/",
        json={"target_type": "post", "target_id": str(uuid4()), "reason": "spam"},
        headers=_auth_headers(user),
    )

    assert response.status_code == 404


def test_regular_user_cannot_list_reports(client, db_session):
    user = _create_user(db_session)

    response = client.get("/api/v1/reports/", headers=_auth_headers(user))

    assert response.status_code == 403


def test_admin_lists_and_resolves_report(client, db_session):
    user = _create_user(db_session)
    admin = _create_user(db_session, username="admin", role="admin")
    board = _create_board(db_session)
    post = _create_post(db_session, author=user, board=board)

    create_response = client.post(
        "/api/v1/reports/",
        json={"target_type": "post", "target_id": str(post.id), "reason": "spam"},
        headers=_auth_headers(user),
    )
    report_id = UUID(create_response.json()["data"]["id"])

    list_response = client.get(
        "/api/v1/reports/?status=pending", headers=_auth_headers(admin)
    )
    assert list_response.status_code == 200
    assert list_response.json()["data"]["pagination"]["total"] == 1

    resolve_response = client.patch(
        f"/api/v1/reports/{report_id}/resolve",
        json={"status": "resolved", "result_note": "confirmed spam"},
        headers=_auth_headers(admin),
    )

    assert resolve_response.status_code == 200
    assert resolve_response.json()["data"]["status"] == "resolved"

    db_session.expire_all()
    report = db_session.query(Report).filter(Report.id == report_id).one()
    hidden_post = db_session.query(Post).filter(Post.id == post.id).one()
    log = (
        db_session.query(ModerationLog)
        .filter(ModerationLog.report_id == report.id)
        .one()
    )

    assert report.handled_by == admin.id
    assert report.result_note == "confirmed spam"
    assert hidden_post.status == "hidden"
    assert log.operator_id == admin.id
    assert log.action == "resolve_report"


def test_cannot_handle_report_twice(client, db_session):
    user = _create_user(db_session)
    admin = _create_user(db_session, username="admin", role="admin")
    board = _create_board(db_session)
    post = _create_post(db_session, author=user, board=board)

    create_response = client.post(
        "/api/v1/reports/",
        json={"target_type": "post", "target_id": str(post.id), "reason": "spam"},
        headers=_auth_headers(user),
    )
    report_id = UUID(create_response.json()["data"]["id"])

    first_response = client.patch(
        f"/api/v1/reports/{report_id}/resolve",
        json={"status": "dismissed", "result_note": "not a violation"},
        headers=_auth_headers(admin),
    )
    second_response = client.patch(
        f"/api/v1/reports/{report_id}/resolve",
        json={"status": "resolved", "result_note": "second attempt"},
        headers=_auth_headers(admin),
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 409
