# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Campus Bulletin Board System (校园论坛) — a campus forum with user auth, posts, comments, likes, and notifications. Python >=3.14 backend (FastAPI), Vue 3 + TypeScript frontend.

## Development Commands

### Start infrastructure
```bash
make deps-up          # Start PostgreSQL, Redis, and Mailpit via Docker Compose
make deps-down        # Stop all services
make deps-logs        # Tail logs for all services
make deps-ps          # Show Docker service status
make deps-reset-db    # Wipe and recreate Postgres volume
make dev              # Start deps + print instructions for backend/frontend
```

Mailpit (SMTP on `localhost:1025`, web UI on `localhost:8025`) catches all dev emails.

### Backend
```bash
cd backend && uv sync                              # Install dependencies
cd backend && uv run uvicorn app.main:app --reload # Dev server (or: make backend)
```

### Frontend
```bash
cd frontend && pnpm install           # Install dependencies
cd frontend && pnpm run dev           # Vite dev server (or: make frontend)
cd frontend && pnpm run build         # Type-check + production build
cd frontend && pnpm run type-check    # vue-tsc type check only
cd frontend && pnpm run preview       # Vite preview of built output
```

### Lint & Format (or use make targets)
```bash
make format              # Format backend (black) + frontend (prettier)
make lint                # Lint backend (ruff) + frontend (oxlint + eslint)
cd frontend && pnpm run lint       # Frontend only
cd backend && uvx ruff check .     # Backend only
cd backend && uvx black .          # Backend only
```

### Database Migrations (Alembic)
Migrations live in `backend/migrations/`. On startup, `init_db()` runs `alembic upgrade head` automatically.
```bash
make migration-new msg="description"   # Generate new migration from model changes
make migrate                           # Apply pending migrations
make migrate-rollback                  # Rollback last migration
make migrate-history                   # View migration history
```

### Tests
```bash
cd backend && uv run pytest                     # All tests
cd backend && uv run pytest tests/test_auth.py  # Single file
cd backend && uv run pytest -k "test_login"     # Single test by name pattern
cd frontend && pnpm run test:unit               # Frontend unit tests (Vitest)
```
Tests use SQLite (file-based per test module) + fakeredis — no Docker services needed.

### Git Hooks
```bash
pnpm install && pnpm run prepare  # Install husky pre-commit (lint-staged: black + ruff)
```

## Architecture

### Backend Layered Structure (`backend/app/`)

```
config.py          → Settings (pydantic-settings, reads .env)
database.py        → SQLAlchemy engine, SessionLocal, init_db() (runs alembic), get_db()
main.py            → FastAPI app, lifespan (calls init_db), registers routers
models/            → SQLAlchemy ORM models (Base, IDMixin, TimestampMixin in base.py)
schemas/           → Pydantic request/response schemas (response.py has ApiResponse/PaginatedResponse/ErrorResponse)
routers/           → FastAPI APIRouter modules (auth, users, boards, posts, comments, likes, notifications, admin)
services/          → Business logic classes (auth_service, user_service, post_service, board_service, email_service)
deps/              → FastAPI Depends providers: get_db, get_current_user + require_admin (auth), get_*_service (services)
utils/             → Helpers: security.py (password hashing), redis.py (Redis client + token blacklist)
```

All routers mount under `/api/v1/{router_prefix}`. Health check at `/health`.

### Key Patterns

- **API responses**: All endpoints wrap data in `ApiResponse[T]` / `PaginatedResponse[T]` / `ErrorResponse` from `schemas/response.py`. Format: `{code, message, data, request_id}`.
- **Auth flow**: JWT (HS256) via PyJWT. Login accepts username or email (`or_()` filter). `get_current_user` checks Redis blacklist → decode JWT → verify user exists, not banned, and email is verified. OAuth2PasswordBearer tokenUrl is `/api/v1/auth/login`.
- **Email verification**: On register, `AuthService` calls `EmailService.send_verification_email()` (token via JWT with `type="email_verify"`). Unverified users cannot log in (`email_verified` field on User model). Verify endpoint: `POST /api/v1/auth/verify-email`.
- **Token blacklist**: `utils/redis.py` blacklists JWTs on logout under key `token_blacklist:{sha256(token)}` with TTL = remaining validity. `get_redis()` returns a lazy-initialized singleton `redis.Redis` instance.
- **DB models**: Use `IDMixin` (UUID pk) + `TimestampMixin` (created_at/updated_at/deleted_at). Soft delete via `deleted_at` field. Services filter `deleted_at.is_(None)` when querying.
- **User model**: Has `email_verified: bool` (default False), `role: str` ("user" | "admin"), `status: str` ("active" | "banned").
- **Post model**: Has `is_pinned`, `is_featured`, `status` (PostStatus enum: NORMAL/HIDDEN/DELETED), `published_at`.
- **Board model**: Has `slug: str` and `sort_order: int`.
- **Dependency injection**: Routers inject `db: Session` and `service` instances via `Depends()` from `deps/`. Services are stateless — `Session` is passed per-method.
- **Password hashing**: `pwdlib.PasswordHash.recommended()` via `utils/security.py`.

### Services

| Service | File | Key Methods |
|---------|------|-------------|
| `AuthService` | `services/auth_service.py` | register, login, logout, reset_password |
| `UserService` | `services/user_service.py` | get_profile, update_profile, get_public_profile, list_users, update_status |
| `PostService` | `services/post_service.py` | create, get_multi (eager-loads author, sorted by is_pinned DESC, created_at DESC), get_by_id, update (partial via exclude_unset), update_special_status, remove |
| `BoardService` | `services/board_service.py` | get_all, get_by_id, get_by_slug, create, update, remove |
| `EmailService` | `services/email_service.py` | generate_verify_token, decode_verify_token, send_verification_email (SMTP via Mailpit in dev) |

### Router Status

Fully implemented: `auth`, `users`, `boards`, `posts`, `admin`
Stubs (endpoints defined with `pass`): `comments`, `likes`, `notifications`

Key admin endpoints (all require `require_admin`):
- `GET /admin/stats` — system statistics
- `GET /admin/users` — list all users
- `PATCH /admin/users/{id}/status` — ban/unban users
- `GET/POST /admin/boards`, `PATCH/DELETE /admin/boards/{id}` — board CRUD

### Code Duplication

`create_access_token()` is defined in both `deps/auth.py` (public) and `services/auth_service.py` (private `_create_access_token`). If modifying JWT logic, update both.

## Key Config

`backend/app/config.py` reads from `.env`. No committed `.env.example`. Key defaults:

| Variable | Default | Purpose |
|----------|---------|---------|
| `DATABASE_URL` | `postgresql+psycopg2://bbs_user:bbs_password@localhost:5432/bbs` | Postgres connection |
| `REDIS_HOST` / `REDIS_PORT` / `REDIS_DB` | `localhost` / `6379` / `0` | Redis connection |
| `JWT_SECRET` | (dev default) | HS256 signing key |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | Access token TTL |
| `FRONTEND_BASE_URL` | `http://localhost:5173` | Used in verification emails |
| `BACKEND_BASE_URL` | `http://localhost:8000` | Backend self-URL |
| `SMTP_HOST` / `SMTP_PORT` | `localhost` / `1025` | Mailpit in dev |
| `SMTP_FROM` | `noreply@campus-bbs.local` | Email sender |
| `EMAIL_VERIFY_TOKEN_EXPIRE_MINUTES` | `1440` (24h) | Verification link TTL |

## Test Infrastructure

Tests use **SQLite file-based** (one DB per test module) and **fakeredis**, so no Docker services needed.

Pattern (repeated in each test file — not centralized in conftest.py):
- `conftest.py` only does one thing: autouse fixture that swaps `app.utils.redis._redis` with `fakeredis.FakeRedis`
- Each test file defines its own SQLite engine, `TestingSessionLocal`, `_setup_db` fixture (`Base.metadata.create_all` / `drop_all`), and `_override_get_db()` dependency override
- `app.dependency_overrides[get_db]` — injects test DB session
- `_make_mock_email_service()` — creates an `EmailService` with `send_verification_email` mocked (but real JWT token generation), injected via `app.dependency_overrides[get_email_service]`
- `test_auth.py` and `test_users.py` use synchronous `TestClient`; `test_admin.py` uses `AsyncClient` + `pytest.mark.asyncio`

## Frontend

Vue 3 + TypeScript + Vite project in `frontend/`. Currently scaffolded with router and stores in place but no pages implemented yet.

```
frontend/src/
  main.ts           → App entry (creates Vue app with Pinia + Router)
  App.vue           → Root component
  router/index.ts   → Vue Router with createWebHistory (routes array empty)
  stores/           → Pinia stores
  __tests__/        → Vitest tests
```

Key commands: `pnpm run dev` (Vite on 5173), `pnpm run build`, `pnpm run test:unit` (Vitest), `pnpm run type-check` (vue-tsc), `pnpm run lint` (oxlint + eslint).

## Database Design

Full schema spec in `docs/DatabaseDesign.md`. Core tables: users, boards, posts, comments, post_likes, comment_likes, media_assets, post_attachments, notifications. All PKs are UUID. Connection defaults: Postgres `localhost:5432` (db=bbs, user=bbs_user, pass=bbs_password), Redis `localhost:6379`.

## Design Documentation

- `docs/DatabaseDesign.md` — Full table specs, ER diagrams, naming conventions
- `docs/DevelopmentSpecification.md` — Tech stack, Git conventions, API conventions, code style
- `docs/ComponentDesign.md` — Detailed component design (layered architecture, class diagrams, state machines)
- `docs/SystemDesign.md` — System-level design
- `docs/KeyProcessDescription.md` — Key process flows
- `docs/RequirementAnalysis.md` — Requirements
- `docs/ProjectPlan.md` — Project plan
- `docs/diagrams/` — Mermaid diagrams (class, ER, state machine, architecture, data flow, use case, Gantt)

## Git Conventions

- Branches: `feat/<subsystem>-<feature>-<date>`, `fix/`, `refactor/`, `docs/`
- Commits: `<type>(<scope>): <subject>` — types: feat, fix, refactor, docs, test, chore
- Flow: feature branch → develop (PR with review) → main (lead merges)
- Pre-commit hook runs lint-staged (black + ruff --fix on backend/**/*.py)

## API Conventions

RESTful under `/api/v1/`. PATCH for partial updates. HTTP status codes follow spec in `docs/DevelopmentSpecification.md` (200/201/204/400/401/403/404/409/422/429/500).
