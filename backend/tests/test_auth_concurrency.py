"""
Concurrency / race-condition tests for Auth (registration).

Covers duplicate-username and duplicate-email races where two concurrent
registrations both pass the app-level check before either commits.
Uses ThreadPoolExecutor + monkeypatch delays.
"""

import time
from unittest.mock import Mock

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from app.database import get_db
from app.deps import get_email_service
from app.main import app
from app.models.base import Base
from app.models.user import User
from app.schemas.auth import AuthUserData, RegisterData
from app.services.auth_service import AuthService
from app.services.email_service import EmailService
from app.utils.security import hash_password
from tests.concurrency_utils import race_requests

SQLALCHEMY_DATABASE_URL = "sqlite:///test_auth_concurrency.db"

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


# ── Registration race tests ────────────────────────────────────────


class TestRegistrationConcurrency:
    def test_same_username_race(self, client, db_session, monkeypatch):
        """2 concurrent registrations with same username, different emails.
        One succeeds, one gets 409 (IntegrityError on DB unique constraint).
        """

        # Inject delay between app-level check and db write
        def delayed_register(self, db, payload, email_service):
            existing = (
                db.query(User)
                .filter(
                    or_(User.username == payload.username, User.email == payload.email),
                    User.deleted_at.is_(None),
                )
                .first()
            )
            if existing and existing.username == payload.username:
                raise HTTPException(status_code=409, detail="Username already exists")
            if existing and existing.email == payload.email:
                raise HTTPException(status_code=409, detail="Email already exists")

            time.sleep(0.05)

            user = User(
                username=payload.username,
                email=str(payload.email),
                password_hash=hash_password(payload.password),
                nickname=payload.nickname or None,
            )
            db.add(user)
            try:
                db.commit()
            except IntegrityError:
                db.rollback()
                raise HTTPException(
                    status_code=409, detail="Username or email already exists"
                )
            except Exception:
                db.rollback()
                raise
            db.refresh(user)

            try:
                verify_token = email_service.generate_verify_token(
                    str(user.id), user.email
                )
                email_service.send_verification_email(user.email, verify_token)
            except Exception:
                db.rollback()
                raise

            return RegisterData(
                user=AuthUserData(
                    id=str(user.id),
                    username=user.username,
                    email=user.email,
                    nickname=user.nickname,
                    role=user.role,
                    status=user.status,
                )
            )

        monkeypatch.setattr(AuthService, "register", delayed_register)

        def register_1():
            c = TestClient(app)
            return c.post(
                f"{AUTH_PREFIX}/register",
                json={
                    "username": "racer",
                    "email": "racer1@test.com",
                    "password": "securepass123",
                },
            )

        def register_2():
            c = TestClient(app)
            return c.post(
                f"{AUTH_PREFIX}/register",
                json={
                    "username": "racer",
                    "email": "racer2@test.com",
                    "password": "securepass123",
                },
            )

        responses = race_requests([register_1, register_2])

        statuses = [r.status_code for r in responses]
        assert 200 in statuses, f"Expected at least one 200, got {statuses}"
        assert 409 in statuses, f"Expected at least one 409, got {statuses}"

        # Only one user with this username should exist
        users = (
            db_session.query(User)
            .filter(User.username == "racer", User.deleted_at.is_(None))
            .count()
        )
        assert users == 1, f"Expected 1 user, got {users}"

    def test_same_email_race(self, client, db_session, monkeypatch):
        """2 concurrent registrations with same email, different usernames.
        One succeeds, one gets 409.
        """

        def delayed_register(self, db, payload, email_service):
            existing = (
                db.query(User)
                .filter(
                    or_(User.username == payload.username, User.email == payload.email),
                    User.deleted_at.is_(None),
                )
                .first()
            )
            if existing and existing.username == payload.username:
                raise HTTPException(status_code=409, detail="Username already exists")
            if existing and existing.email == payload.email:
                raise HTTPException(status_code=409, detail="Email already exists")

            time.sleep(0.05)

            user = User(
                username=payload.username,
                email=str(payload.email),
                password_hash=hash_password(payload.password),
                nickname=payload.nickname or None,
            )
            db.add(user)
            try:
                db.commit()
            except IntegrityError:
                db.rollback()
                raise HTTPException(
                    status_code=409, detail="Username or email already exists"
                )
            except Exception:
                db.rollback()
                raise
            db.refresh(user)

            try:
                verify_token = email_service.generate_verify_token(
                    str(user.id), user.email
                )
                email_service.send_verification_email(user.email, verify_token)
            except Exception:
                db.rollback()
                raise

            return RegisterData(
                user=AuthUserData(
                    id=str(user.id),
                    username=user.username,
                    email=user.email,
                    nickname=user.nickname,
                    role=user.role,
                    status=user.status,
                )
            )

        monkeypatch.setattr(AuthService, "register", delayed_register)

        def register_1():
            c = TestClient(app)
            return c.post(
                f"{AUTH_PREFIX}/register",
                json={
                    "username": "email_racer_1",
                    "email": "same@test.com",
                    "password": "securepass123",
                },
            )

        def register_2():
            c = TestClient(app)
            return c.post(
                f"{AUTH_PREFIX}/register",
                json={
                    "username": "email_racer_2",
                    "email": "same@test.com",
                    "password": "securepass123",
                },
            )

        responses = race_requests([register_1, register_2])

        statuses = [r.status_code for r in responses]
        assert 200 in statuses, f"Expected at least one 200, got {statuses}"
        assert 409 in statuses, f"Expected at least one 409, got {statuses}"

        users = (
            db_session.query(User)
            .filter(User.email == "same@test.com", User.deleted_at.is_(None))
            .count()
        )
        assert users == 1, f"Expected 1 user, got {users}"

    def test_different_users_succeeds(self, client, db_session):
        """2 concurrent registrations with different credentials — both should succeed.
        Sanity check that the concurrency harness doesn't produce false positives.
        """

        def register_1():
            c = TestClient(app)
            return c.post(
                f"{AUTH_PREFIX}/register",
                json={
                    "username": "unique_a",
                    "email": "unique_a@test.com",
                    "password": "securepass123",
                },
            )

        def register_2():
            c = TestClient(app)
            return c.post(
                f"{AUTH_PREFIX}/register",
                json={
                    "username": "unique_b",
                    "email": "unique_b@test.com",
                    "password": "securepass123",
                },
            )

        responses = race_requests([register_1, register_2])

        statuses = [r.status_code for r in responses]
        assert all(s == 200 for s in statuses), f"Expected both 200, got {statuses}"

        total = db_session.query(User).filter(User.deleted_at.is_(None)).count()
        assert total == 2, f"Expected 2 users, got {total}"
