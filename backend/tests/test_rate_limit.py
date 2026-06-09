import pytest
import redis
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import get_db
from app.deps.auth import create_access_token
from app.main import app
from app.models.base import Base
from app.models.board import Board
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


@pytest.fixture(autouse=True)
def _enable_rate_limit(monkeypatch):
    import app.utils.rate_limit as rate_limit_mod

    monkeypatch.setattr(rate_limit_mod.settings, "RATE_LIMIT_ENABLED", True)


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


def _create_user(db, *, username: str = "user") -> User:
    user = User(
        username=username,
        email=f"{username}@example.com",
        password_hash="hashed-password",
        role="user",
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


def test_login_rate_limit_by_ip(client):
    payload = {"account": "missing", "password": "wrong"}
    responses = [client.post("/api/v1/auth/login", json=payload) for _ in range(6)]

    assert [response.status_code for response in responses[:5]] == [401] * 5
    assert responses[5].status_code == 429
    assert responses[5].headers["X-RateLimit-Limit"] == "5"
    assert responses[5].headers["X-RateLimit-Remaining"] == "0"
    assert "X-RateLimit-Reset" in responses[5].headers


def test_post_rate_limit_by_user(client, db_session):
    user = _create_user(db_session)
    board = _create_board(db_session)
    headers = _auth_headers(user)

    for index in range(10):
        response = client.post(
            "/api/v1/posts/",
            json={
                "title": f"post {index}",
                "content": "content",
                "board_id": str(board.id),
            },
            headers=headers,
        )
        assert response.status_code == 201
        assert response.headers["X-RateLimit-Limit"] == "10"

    limited_response = client.post(
        "/api/v1/posts/",
        json={
            "title": "limited",
            "content": "content",
            "board_id": str(board.id),
        },
        headers=headers,
    )

    assert limited_response.status_code == 429
    assert limited_response.headers["X-RateLimit-Remaining"] == "0"


def test_rate_limit_fails_open_when_redis_unavailable(client, monkeypatch):
    import app.utils.rate_limit as rate_limit_mod

    def raise_redis_error():
        raise redis.RedisError("redis unavailable")

    monkeypatch.setattr(rate_limit_mod, "get_redis", raise_redis_error)

    payload = {"account": "missing", "password": "wrong"}
    responses = [client.post("/api/v1/auth/login", json=payload) for _ in range(6)]

    assert [response.status_code for response in responses] == [401] * 6
