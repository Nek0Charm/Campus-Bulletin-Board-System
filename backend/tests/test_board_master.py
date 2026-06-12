"""
BoardMaster + Mute 集成测试：版主权限、CRUD、禁言

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
from app.models.board import Board
from app.models.user import User
from app.utils.security import hash_password

SQLALCHEMY_DATABASE_URL = "sqlite:///test_board_master.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

API_PREFIX = "/api/v1"
POSTS_URL = f"{API_PREFIX}/posts"
POSTS_LIST = f"{POSTS_URL}/"
COMMENTS_URL = f"{API_PREFIX}/comments"
COMMENTS_LIST = f"{COMMENTS_URL}/"
AUTH_PREFIX = f"{API_PREFIX}/auth"
BOARDS_URL = f"{API_PREFIX}/boards"
ADMIN_URL = f"{API_PREFIX}/admin"

POST_PAYLOAD = {"title": "Test Title", "content": "Hello world"}


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


# ---------- helpers ----------


def _create_user(
    db, username: str, email: str, role: str = "user", email_verified: bool = True
) -> User:
    user = User(
        username=username,
        email=email,
        password_hash=hash_password("securepass123"),
        nickname=username,
        role=role,
        status="active",
        email_verified=email_verified,
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


async def _login(client: AsyncClient, account: str) -> str:
    resp = await client.post(
        f"{AUTH_PREFIX}/login",
        json={"account": account, "password": "securepass123"},
    )
    return resp.json()["data"]["access_token"]


async def _get_auth_client(client: AsyncClient, token: str) -> AsyncClient:
    transport = ASGITransport(app=app)
    return AsyncClient(
        transport=transport,
        base_url="http://test",
        headers={"Authorization": f"Bearer {token}"},
    )


async def _prepare_user_and_board(client, db_session, username="poster", role="user"):
    user = _create_user(db_session, username, f"{username}@test.com", role=role)
    token = await _login(client, username)
    ac = await _get_auth_client(client, token)
    board = _create_board(db_session, f"bd-{username}", f"slug-{username}")
    return ac, user, board


async def _make_board_master(
    admin_client: AsyncClient, board_id: str, user_id: str
) -> dict:
    resp = await admin_client.post(
        f"{ADMIN_URL}/boards/{board_id}/masters",
        json={"user_id": user_id},
    )
    return resp.json()["data"]


async def _create_post(
    client: AsyncClient, board_id: str, title: str = "Test Post"
) -> dict:
    resp = await client.post(
        POSTS_LIST, json={**POST_PAYLOAD, "title": title, "board_id": board_id}
    )
    return resp.json()["data"]


# =============================== Board Master CRUD ===============================


@pytest.mark.asyncio
async def test_admin_can_add_board_master(client: AsyncClient, db_session):
    admin_ac, _, board = await _prepare_user_and_board(
        client, db_session, "bm_admin", "admin"
    )
    normal_ac, user, _ = await _prepare_user_and_board(
        client, db_session, "bm_user", "user"
    )

    resp = await admin_ac.post(
        f"{ADMIN_URL}/boards/{board.id}/masters",
        json={"user_id": str(user.id)},
    )
    assert resp.status_code == status.HTTP_201_CREATED
    data = resp.json()["data"]
    assert data["board_id"] == str(board.id)
    assert data["user_id"] == str(user.id)
    assert data["user"]["username"] == "bm_user"


@pytest.mark.asyncio
async def test_admin_list_board_masters(client: AsyncClient, db_session):
    admin_ac, _, board = await _prepare_user_and_board(
        client, db_session, "bl_admin", "admin"
    )
    normal_ac, user, _ = await _prepare_user_and_board(
        client, db_session, "bl_user", "user"
    )
    await _make_board_master(admin_ac, str(board.id), str(user.id))

    resp = await admin_ac.get(f"{ADMIN_URL}/boards/{board.id}/masters")
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()["data"]
    assert len(data) == 1
    assert data[0]["user"]["username"] == "bl_user"


@pytest.mark.asyncio
async def test_admin_remove_board_master(client: AsyncClient, db_session):
    admin_ac, _, board = await _prepare_user_and_board(
        client, db_session, "br_admin", "admin"
    )
    normal_ac, user, _ = await _prepare_user_and_board(
        client, db_session, "br_user", "user"
    )
    await _make_board_master(admin_ac, str(board.id), str(user.id))

    resp = await admin_ac.delete(f"{ADMIN_URL}/boards/{board.id}/masters/{user.id}")
    assert resp.status_code == status.HTTP_200_OK

    # Verify removed
    resp = await admin_ac.get(f"{ADMIN_URL}/boards/{board.id}/masters")
    assert len(resp.json()["data"]) == 0


@pytest.mark.asyncio
async def test_add_board_master_duplicate_restores(client: AsyncClient, db_session):
    admin_ac, _, board = await _prepare_user_and_board(
        client, db_session, "bd_admin", "admin"
    )
    normal_ac, user, _ = await _prepare_user_and_board(
        client, db_session, "bd_user", "user"
    )
    await _make_board_master(admin_ac, str(board.id), str(user.id))
    # Remove
    await admin_ac.delete(f"{ADMIN_URL}/boards/{board.id}/masters/{user.id}")
    # Re-add (should restore, not fail)
    resp = await admin_ac.post(
        f"{ADMIN_URL}/boards/{board.id}/masters",
        json={"user_id": str(user.id)},
    )
    assert resp.status_code == status.HTTP_201_CREATED


@pytest.mark.asyncio
async def test_non_admin_cannot_manage_masters(client: AsyncClient, db_session):
    normal_ac, user, board = await _prepare_user_and_board(
        client, db_session, "bn_admin", "user"
    )

    resp = await normal_ac.post(
        f"{ADMIN_URL}/boards/{board.id}/masters",
        json={"user_id": str(user.id)},
    )
    assert resp.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_add_board_master_nonexistent_user(client: AsyncClient, db_session):
    admin_ac, _, board = await _prepare_user_and_board(
        client, db_session, "bnu_admin", "admin"
    )
    resp = await admin_ac.post(
        f"{ADMIN_URL}/boards/{board.id}/masters",
        json={"user_id": str(uuid.uuid4())},
    )
    assert resp.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_add_board_master_nonexistent_board(client: AsyncClient, db_session):
    admin_ac, _, _ = await _prepare_user_and_board(
        client, db_session, "bnb_admin", "admin"
    )
    normal_ac, user, _ = await _prepare_user_and_board(
        client, db_session, "bnb_user", "user"
    )
    resp = await admin_ac.post(
        f"{ADMIN_URL}/boards/{uuid.uuid4()}/masters",
        json={"user_id": str(user.id)},
    )
    assert resp.status_code == status.HTTP_404_NOT_FOUND


# =============================== Board Master Pin/Feature ===============================


@pytest.mark.asyncio
async def test_board_master_can_pin_post_in_their_board(
    client: AsyncClient, db_session
):
    admin_ac, _, board = await _prepare_user_and_board(
        client, db_session, "bmp_admin", "admin"
    )
    bm_ac, bm_user, _ = await _prepare_user_and_board(
        client, db_session, "bmp_master", "user"
    )
    # Author creates post
    author_ac, author_user, _ = await _prepare_user_and_board(
        client, db_session, "bmp_author", "user"
    )
    # Make bm_master a board master
    await _make_board_master(admin_ac, str(board.id), str(bm_user.id))
    # Author posts in board
    post = await _create_post(author_ac, str(board.id), "BM Pin Test")

    # Board master pins it
    resp = await bm_ac.patch(f"{POSTS_URL}/{post['id']}/pin", json={"is_pinned": True})
    assert resp.status_code == status.HTTP_200_OK
    assert resp.json()["data"]["is_pinned"] is True


@pytest.mark.asyncio
async def test_board_master_cannot_pin_post_in_other_board(
    client: AsyncClient, db_session
):
    admin_ac, _, board_a = await _prepare_user_and_board(
        client, db_session, "bmo_admin", "admin"
    )
    bm_ac, bm_user, _ = await _prepare_user_and_board(
        client, db_session, "bmo_master", "user"
    )
    board_b = _create_board(db_session, "Other Board", "other-board")
    author_ac, _, _ = await _prepare_user_and_board(
        client, db_session, "bmo_author", "user"
    )
    # Make bm_master a master of board_a only
    await _make_board_master(admin_ac, str(board_a.id), str(bm_user.id))
    # Post in board_b (where bm_user is NOT a master)
    post = await _create_post(author_ac, str(board_b.id), "Other Board Post")

    resp = await bm_ac.patch(f"{POSTS_URL}/{post['id']}/pin", json={"is_pinned": True})
    assert resp.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_board_master_can_feature_post_in_their_board(
    client: AsyncClient, db_session
):
    admin_ac, _, board = await _prepare_user_and_board(
        client, db_session, "bmf_admin", "admin"
    )
    bm_ac, bm_user, _ = await _prepare_user_and_board(
        client, db_session, "bmf_master", "user"
    )
    author_ac, _, _ = await _prepare_user_and_board(
        client, db_session, "bmf_author", "user"
    )
    await _make_board_master(admin_ac, str(board.id), str(bm_user.id))
    post = await _create_post(author_ac, str(board.id), "BM Feature Test")

    resp = await bm_ac.patch(
        f"{POSTS_URL}/{post['id']}/feature", json={"is_featured": True}
    )
    assert resp.status_code == status.HTTP_200_OK
    assert resp.json()["data"]["is_featured"] is True


@pytest.mark.asyncio
async def test_board_master_cannot_feature_post_in_other_board(
    client: AsyncClient, db_session
):
    admin_ac, _, board_a = await _prepare_user_and_board(
        client, db_session, "bmfo_admin", "admin"
    )
    bm_ac, bm_user, _ = await _prepare_user_and_board(
        client, db_session, "bmfo_master", "user"
    )
    board_b = _create_board(db_session, "Other Board 2", "other-board-2")
    author_ac, _, _ = await _prepare_user_and_board(
        client, db_session, "bmfo_author", "user"
    )
    await _make_board_master(admin_ac, str(board_a.id), str(bm_user.id))
    post = await _create_post(author_ac, str(board_b.id), "Other Board Post 2")

    resp = await bm_ac.patch(
        f"{POSTS_URL}/{post['id']}/feature", json={"is_featured": True}
    )
    assert resp.status_code == status.HTTP_403_FORBIDDEN


# =============================== Board Master Delete ===============================


@pytest.mark.asyncio
async def test_board_master_can_delete_post_in_their_board(
    client: AsyncClient, db_session
):
    admin_ac, _, board = await _prepare_user_and_board(
        client, db_session, "bmd_admin", "admin"
    )
    bm_ac, bm_user, _ = await _prepare_user_and_board(
        client, db_session, "bmd_master", "user"
    )
    author_ac, _, _ = await _prepare_user_and_board(
        client, db_session, "bmd_author", "user"
    )
    await _make_board_master(admin_ac, str(board.id), str(bm_user.id))
    post = await _create_post(author_ac, str(board.id), "BM Delete Test")

    resp = await bm_ac.delete(f"{POSTS_URL}/{post['id']}")
    assert resp.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test_board_master_cannot_delete_post_in_other_board(
    client: AsyncClient, db_session
):
    admin_ac, _, board_a = await _prepare_user_and_board(
        client, db_session, "bmdo_admin", "admin"
    )
    bm_ac, bm_user, _ = await _prepare_user_and_board(
        client, db_session, "bmdo_master", "user"
    )
    board_b = _create_board(db_session, "Other Board 3", "other-board-3")
    author_ac, _, _ = await _prepare_user_and_board(
        client, db_session, "bmdo_author", "user"
    )
    await _make_board_master(admin_ac, str(board_a.id), str(bm_user.id))
    post = await _create_post(author_ac, str(board_b.id), "Other Board Post 3")

    resp = await bm_ac.delete(f"{POSTS_URL}/{post['id']}")
    assert resp.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_regular_user_still_cannot_pin(client: AsyncClient, db_session):
    """Regression: regular user (not board master) still cannot pin"""
    normal_ac, _, board = await _prepare_user_and_board(
        client, db_session, "reg_pin_user", "user"
    )
    post = await _create_post(normal_ac, str(board.id), "Regular Pin Test")

    resp = await normal_ac.patch(
        f"{POSTS_URL}/{post['id']}/pin", json={"is_pinned": True}
    )
    assert resp.status_code == status.HTTP_403_FORBIDDEN


# =============================== Board Master Delete Comment ===============================


@pytest.mark.asyncio
async def test_board_master_can_delete_comment_in_their_board(
    client: AsyncClient, db_session
):
    admin_ac, _, board = await _prepare_user_and_board(
        client, db_session, "bmdc_admin", "admin"
    )
    bm_ac, bm_user, _ = await _prepare_user_and_board(
        client, db_session, "bmdc_master", "user"
    )
    author_ac, _, _ = await _prepare_user_and_board(
        client, db_session, "bmdc_author", "user"
    )
    commenter_ac, _, _ = await _prepare_user_and_board(
        client, db_session, "bmdc_commenter", "user"
    )
    await _make_board_master(admin_ac, str(board.id), str(bm_user.id))
    post = await _create_post(author_ac, str(board.id), "BM Comment Test")

    # Commenter posts comment
    resp = await commenter_ac.post(
        COMMENTS_LIST,
        json={"post_id": post["id"], "content": "A comment"},
    )
    comment_id = resp.json()["data"]["id"]

    # Board master deletes it
    resp = await bm_ac.delete(f"{COMMENTS_URL}/{comment_id}")
    assert resp.status_code == status.HTTP_200_OK


# =============================== Admin Mute ===============================


@pytest.mark.asyncio
async def test_admin_can_mute_user(client: AsyncClient, db_session):
    admin_ac, _, _ = await _prepare_user_and_board(
        client, db_session, "mt_admin", "admin"
    )
    normal_ac, user, _ = await _prepare_user_and_board(
        client, db_session, "mt_user", "user"
    )

    resp = await admin_ac.post(
        f"{ADMIN_URL}/users/{user.id}/mute",
        json={"duration_minutes": 60},
    )
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()["data"]
    assert data["id"] == str(user.id)
    # muted_until should be set


@pytest.mark.asyncio
async def test_admin_can_unmute_user(client: AsyncClient, db_session):
    admin_ac, _, _ = await _prepare_user_and_board(
        client, db_session, "umt_admin", "admin"
    )
    normal_ac, user, _ = await _prepare_user_and_board(
        client, db_session, "umt_user", "user"
    )
    # Mute first
    await admin_ac.post(
        f"{ADMIN_URL}/users/{user.id}/mute",
        json={"duration_minutes": 60},
    )
    # Unmute
    resp = await admin_ac.delete(f"{ADMIN_URL}/users/{user.id}/mute")
    assert resp.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test_muted_user_cannot_create_post(client: AsyncClient, db_session):
    admin_ac, _, _ = await _prepare_user_and_board(
        client, db_session, "mup_admin", "admin"
    )
    normal_ac, user, board = await _prepare_user_and_board(
        client, db_session, "mup_user", "user"
    )
    # Mute the user
    await admin_ac.post(
        f"{ADMIN_URL}/users/{user.id}/mute",
        json={"duration_minutes": 60},
    )
    # User tries to post
    resp = await normal_ac.post(
        POSTS_LIST, json={**POST_PAYLOAD, "board_id": str(board.id)}
    )
    assert resp.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_muted_user_cannot_create_comment(client: AsyncClient, db_session):
    admin_ac, _, board = await _prepare_user_and_board(
        client, db_session, "muc_admin", "admin"
    )
    author_ac, _, _ = await _prepare_user_and_board(
        client, db_session, "muc_author", "user"
    )
    muted_ac, muted_user, _ = await _prepare_user_and_board(
        client, db_session, "muc_muted", "user"
    )
    post = await _create_post(author_ac, str(board.id), "Mute Comment Test")

    # Mute the user
    await admin_ac.post(
        f"{ADMIN_URL}/users/{muted_user.id}/mute",
        json={"duration_minutes": 60},
    )
    # Muted user tries to comment
    resp = await muted_ac.post(
        COMMENTS_LIST,
        json={"post_id": post["id"], "content": "Muted comment"},
    )
    assert resp.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_muted_user_can_still_read_posts(client: AsyncClient, db_session):
    admin_ac, _, board = await _prepare_user_and_board(
        client, db_session, "mur_admin", "admin"
    )
    author_ac, _, _ = await _prepare_user_and_board(
        client, db_session, "mur_author", "user"
    )
    muted_ac, muted_user, _ = await _prepare_user_and_board(
        client, db_session, "mur_muted", "user"
    )
    post = await _create_post(author_ac, str(board.id), "Readable Post")

    # Mute
    await admin_ac.post(
        f"{ADMIN_URL}/users/{muted_user.id}/mute",
        json={"duration_minutes": 60},
    )
    # Muted user can still read
    resp = await muted_ac.get(f"{POSTS_URL}/{post['id']}")
    assert resp.status_code == status.HTTP_200_OK

    # Muted user can still list
    resp = await muted_ac.get(POSTS_LIST)
    assert resp.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test_board_master_can_mute_user_in_their_board(
    client: AsyncClient, db_session
):
    admin_ac, _, board = await _prepare_user_and_board(
        client, db_session, "bmm_admin", "admin"
    )
    bm_ac, bm_user, _ = await _prepare_user_and_board(
        client, db_session, "bmm_master", "user"
    )
    target_ac, target_user, _ = await _prepare_user_and_board(
        client, db_session, "bmm_target", "user"
    )
    await _make_board_master(admin_ac, str(board.id), str(bm_user.id))

    resp = await bm_ac.post(
        f"{BOARDS_URL}/{board.id}/users/{target_user.id}/mute",
        json={"duration_minutes": 30},
    )
    assert resp.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test_board_master_cannot_mute_admin(client: AsyncClient, db_session):
    admin_ac, admin_user, board = await _prepare_user_and_board(
        client, db_session, "bmma_admin", "admin"
    )
    bm_ac, bm_user, _ = await _prepare_user_and_board(
        client, db_session, "bmma_master", "user"
    )
    await _make_board_master(admin_ac, str(board.id), str(bm_user.id))

    resp = await bm_ac.post(
        f"{BOARDS_URL}/{board.id}/users/{admin_user.id}/mute",
        json={"duration_minutes": 30},
    )
    assert resp.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_non_board_master_cannot_mute(client: AsyncClient, db_session):
    admin_ac, _, board = await _prepare_user_and_board(
        client, db_session, "nbm_admin", "admin"
    )
    normal_ac, _, _ = await _prepare_user_and_board(
        client, db_session, "nbm_user", "user"
    )
    target_ac, target_user, _ = await _prepare_user_and_board(
        client, db_session, "nbm_target", "user"
    )

    resp = await normal_ac.post(
        f"{BOARDS_URL}/{board.id}/users/{target_user.id}/mute",
        json={"duration_minutes": 30},
    )
    assert resp.status_code == status.HTTP_403_FORBIDDEN


# =============================== Public Board Masters Endpoint ===============================


@pytest.mark.asyncio
async def test_public_can_list_board_masters(client: AsyncClient, db_session):
    admin_ac, _, board = await _prepare_user_and_board(
        client, db_session, "pbm_admin", "admin"
    )
    normal_ac, user, _ = await _prepare_user_and_board(
        client, db_session, "pbm_user", "user"
    )
    await _make_board_master(admin_ac, str(board.id), str(user.id))

    # Unauthenticated user can see board masters
    resp = await client.get(f"{BOARDS_URL}/{board.id}/masters")
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()["data"]
    assert len(data) == 1
    assert data[0]["user"]["username"] == "pbm_user"


@pytest.mark.asyncio
async def test_list_board_masters_empty(client: AsyncClient, db_session):
    _, _, board = await _prepare_user_and_board(client, db_session, "pbe_user", "user")

    resp = await client.get(f"{BOARDS_URL}/{board.id}/masters")
    assert resp.status_code == status.HTTP_200_OK
    assert resp.json()["data"] == []
