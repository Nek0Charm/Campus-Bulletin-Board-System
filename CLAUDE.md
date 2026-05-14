# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Campus Bulletin Board System (校园论坛) — a campus forum with user auth, posts, comments, likes, and notifications. Python >=3.14 backend (FastAPI), frontend not yet initialized.

## Development Commands

### Start infrastructure
```bash
make deps-up          # Start PostgreSQL + Redis via Docker Compose
make deps-down        # Stop services
make deps-reset-db    # Wipe and recreate Postgres volume
```

### Backend
```bash
cd backend && uv sync                         # Install dependencies
cd backend && uv run uvicorn app.main:app --reload  # Dev server (or: make backend)
```

### Lint & Format
```bash
cd backend && uvx black .       # Format (or: pnpm run format from root)
cd backend && uvx ruff check .  # Lint (or: pnpm run lint from root)
```

### Tests
No tests directory yet. When adding tests, use pytest + httpx inside `backend/tests/`, run with:
```bash
cd backend && uv run pytest                     # All tests
cd backend && uv run pytest tests/test_auth.py  # Single file
cd backend && uv run pytest -k "test_login"     # Single test by name pattern
```

### Git Hooks
```bash
pnpm install && pnpm run prepare  # Install husky pre-commit (lint-staged: black + ruff)
```

## Architecture

### Backend Layered Structure (`backend/app/`)

```
config.py          → Settings (pydantic-settings, reads .env)
database.py        → SQLAlchemy engine, SessionLocal, init_db(), get_db()
main.py            → FastAPI app, lifespan (calls init_db), registers routers
models/            → SQLAlchemy ORM models (Base, IDMixin, TimestampMixin in base.py)
schemas/           → Pydantic request/response schemas (response.py has ApiResponse/PaginatedResponse/ErrorResponse)
routers/           → FastAPI APIRouter modules (auth, users, boards, posts, comments, likes, notifications, admin)
services/          → Business logic classes (e.g. AuthService)
deps/              → FastAPI Depends providers: get_db, get_current_user, require_admin, get_auth_service
utils/             → Helpers (security.py: hash_password, verify_password via pwdlib)
```

All routers mount under `/api/v1/{router_prefix}`. Health check at `/health`.

### Key Patterns

- **API responses**: All endpoints wrap data in `ApiResponse[T]` / `PaginatedResponse[T]` / `ErrorResponse` from `schemas/response.py`. Format: `{code, message, data, request_id}`.
- **Auth flow**: JWT (HS256) via PyJWT. Login accepts username or email (`or_()` filter). `deps/auth.py` provides `get_current_user` (checks Redis blacklist → decode JWT → verify user exists and not banned) and `require_admin` (wraps get_current_user + role check). OAuth2PasswordBearer tokenUrl is `/api/v1/auth/login`.
- **Logout**: Token is blacklisted in Redis under key `token_blacklist:{sha256(token)}` with TTL = remaining validity.
- **DB models**: Use `IDMixin` (UUID pk, `uuid.uuid4()`) + `TimestampMixin` (created_at/updated_at/deleted_at). Soft delete via `deleted_at` field. All services filter `deleted_at.is_(None)` when querying.
- **Dependency injection**: Routers inject `db: Session` and `service` instances via `Depends()` from `deps/`. Services are stateless — `Session` is passed per-method.
- **PostService specifics**: `get_multi` uses `joinedload(Post.author)` for eager loading, orders by `is_pinned DESC, created_at DESC`. `update` uses `model_dump(exclude_unset=True)` for partial updates. `remove` sets both `deleted_at=now()` and `status=PostStatus.DELETED`.
- **Password hashing**: `pwdlib.PasswordHash.recommended()` via `utils/security.py`.

### Test Infrastructure

Tests use **SQLite in-memory** (not PostgreSQL) and **fakeredis** (not real Redis), so no Docker services needed.

Key patterns in test files:
- `Base.metadata.create_all(bind=engine)` in autouse fixture — creates/drops tables per test
- `app.dependency_overrides[get_db]` — injects test DB session into the FastAPI app
- `test_auth.py` and `test_users.py` use synchronous `TestClient`; `test_admin.py` uses `AsyncClient` + `pytest.mark.asyncio`
- `conftest.py` auto-patches `app.utils.redis._redis` with `fakeredis.FakeRedis` for all tests
- Helper `_register_and_login(client)` registers a user then logs in, returns `(token, user_id)`
- Helper `_register_and_login_admin(client, db_session)` additionally sets `user.role = "admin"` via direct DB write

### Services Implemented

| Service | File | Status |
|---------|------|--------|
| `AuthService` | `services/auth_service.py` | register, login, logout, reset_password |
| `UserService` | `services/user_service.py` | get_profile, update_profile, get_public_profile, list_users, update_status |
| `PostService` | `services/post_service.py` | create, get_multi, get_by_id, update, update_special_status, remove |
| `BoardService` | `services/board_service.py` | get_all, get_by_id, get_by_slug, create, update, remove |

### Code Duplication

`create_access_token()` is defined in both `deps/auth.py` (public) and `services/auth_service.py` (private `_create_access_token`). If modifying JWT logic, update both.

## Database Design

Full schema spec in `docs/DatabaseDesign.md`. Core tables: users, boards, posts, comments, post_likes, comment_likes, media_assets, post_attachments, notifications. All PKs are UUID with `gen_random_uuid()`. Connection defaults: Postgres `localhost:5432` (db=bbs, user=bbs_user, pass=bbs_password), Redis `localhost:6379`.

## Design Documentation

- `docs/DatabaseDesign.md` — Full table specs, ER diagrams, naming conventions
- `docs/DevelopmentSpecification.md` — Tech stack, Git conventions, API conventions, code style
- `docs/ComponentDesign.md` — Detailed component design (layered architecture, class diagrams, state machines)

## Git Conventions

- Branches: `feat/<subsystem>-<feature>-<date>`, `fix/`, `refactor/`, `docs/`
- Commits: `<type>(<scope>): <subject>` — types: feat, fix, refactor, docs, test, chore
- Flow: feature branch → develop (PR with review) → main (lead merges)
- Pre-commit hook runs lint-staged (black + ruff --fix on backend/**/*.py)

## Frontend

`frontend/` is currently a placeholder (`.gitkeep` only). Planned: Vue 3 + TypeScript + Element Plus + Vite. No frontend code exists yet.

## API Conventions

RESTful under `/api/v1/`. PATCH for partial updates. HTTP status codes follow spec in `docs/DevelopmentSpecification.md` (200/201/204/400/401/403/404/409/422/429/500).
