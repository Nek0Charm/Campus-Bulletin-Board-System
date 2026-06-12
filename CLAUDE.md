# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Campus Bulletin Board System (校园论坛) — a campus forum with user auth, posts, comments, likes, and notifications. Python >=3.14 backend (FastAPI), Vue 3 + TypeScript + Element Plus frontend.

## Development Commands

### First-time setup
```bash
make setup-env    # Copy .env.example → .env, generate JWT_SECRET + GARAGE_RPC_SECRET (run before deps-up)
make deps-up      # Start PostgreSQL, Redis, Mailpit, and Garage via Docker Compose
make init-garage  # Initialize Garage S3 storage (run once after first `deps-up`)
make dev          # Start deps + print instructions for backend/frontend
```

Two committed `.env.example` files exist (root and `backend/`). Root `.env.example` covers docker-compose vars; backend's covers app config. `make setup-env` copies root `.env.example` → `.env` and auto-generates secrets.

Mailpit (SMTP on `localhost:1025`, web UI on `localhost:8025`) catches all dev emails.

### Infrastructure management
```bash
make deps-down        # Stop all services
make deps-logs        # Tail logs for all services
make deps-ps          # Show Docker service status
make deps-reset-db    # Wipe and recreate Postgres volume
```

### Backend
```bash
cd backend && uv sync                              # Install dependencies
cd backend && uv run uvicorn app.main:app --reload # Dev server (or: make backend)
```

### Frontend
```bash
cd frontend && pnpm install           # Install dependencies (Node >=20.19.0 || >=22.12.0)
cd frontend && pnpm run dev           # Vite dev server on port 5173 (or: make frontend)
cd frontend && pnpm run build         # Type-check + production build
cd frontend && pnpm run type-check    # vue-tsc type check only
cd frontend && pnpm run preview       # Vite preview of built output
```

Vite dev server proxies `/api/v1` to `http://localhost:8000` — no CORS issues in dev.

### Lint & Format
```bash
make format              # Format backend (black) + frontend (prettier)
make lint                # Lint backend (ruff) + frontend (oxlint + eslint)
cd frontend && pnpm run lint       # Frontend only
cd backend && uvx ruff check .     # Backend only
cd backend && uvx black .          # Backend only
```

### Database Migrations (Alembic)
Migrations live in `backend/migrations/`. Alembic reads `DATABASE_URL` dynamically from `app.config.Settings` (not from `alembic.ini`). On startup, `init_db()` runs `alembic upgrade head` automatically.
```bash
make migration-new msg="description"   # Generate new migration from model changes
make migrate                           # Apply pending migrations
make migrate-rollback                  # Rollback last migration
make migrate-history                   # View migration history
```

### Tests
```bash
cd backend && uv run pytest                     # All backend tests
cd backend && uv run pytest tests/test_auth.py  # Single file
cd backend && uv run pytest -k "test_login"     # Single test by name pattern
cd backend && uv run pytest -m asyncio          # Async tests only
cd frontend && pnpm run test:unit               # Frontend unit tests (Vitest)
cd frontend && pnpm run test:e2e                # E2E tests (Playwright, needs running backend)
cd frontend && pnpm run test:e2e:headed         # E2E tests with browser UI
make test-e2e                                   # E2E via Makefile
```

Backend tests use SQLite (file-based per test module) + fakeredis — no Docker services needed. E2E tests require PostgreSQL + Redis + Mailpit + Backend + Frontend all running. Set `E2E_ADMIN_TOKEN` env var for admin tests.

### Git Hooks
```bash
pnpm install && pnpm run prepare  # Install husky pre-commit (lint-staged: black + ruff)
```

## Architecture

### Backend Layered Structure (`backend/app/`)

```
config.py          → Settings (pydantic-settings, reads .env)
database.py        → SQLAlchemy engine, SessionLocal, init_db() (runs alembic), get_db()
main.py            → FastAPI app, lifespan (calls init_db), registers routers, CORS middleware
models/            → SQLAlchemy ORM models (Base, IDMixin, TimestampMixin in base.py)
schemas/           → Pydantic request/response schemas (response.py has ApiResponse/PaginatedResponse/ErrorResponse)
routers/           → FastAPI APIRouter modules (auth, users, boards, posts, comments, likes, notifications, admin, media, search, announcements)
services/          → Business logic classes (auth, user, post, board, comment, like, notification, email, media, search, announcement, board_master)
deps/              → FastAPI Depends providers: get_db, get_current_user, get_optional_current_user, require_admin, check_not_muted, check_can_moderate_post/board, get_*_service
utils/             → Helpers: security.py (pwdlib[argon2] password hashing), redis.py (Redis client + token blacklist), search.py (jieba tokenization with regex fallback)
storage/           → S3-compatible object storage abstraction (base.py ABC, s3.py boto3 impl, memory.py test impl, factory.py singleton)
```

All routers mount under `/api/v1/{router_prefix}`. Health check at `/health`.

### Key Backend Patterns

- **API responses**: All endpoints wrap data in `ApiResponse[T]` / `PaginatedResponse[T]` / `ErrorResponse` from `schemas/response.py`. Format: `{code, message, data, request_id}`.
- **Auth flow**: JWT (HS256) via PyJWT. Login accepts username or email (`or_()` filter). `get_current_user` checks Redis blacklist → decode JWT → verify user exists, not banned, and email is verified. OAuth2PasswordBearer tokenUrl is `/api/v1/auth/login`. `get_optional_current_user` returns `User | None` (no 401 if missing token) for endpoints accessible to both authenticated and anonymous users.
- **Email verification**: On register, `AuthService` calls `EmailService.send_verification_email()` (token via JWT with `type="email_verify"`). Unverified users cannot log in (`email_verified` field on User model). Verify endpoint: `POST /api/v1/auth/verify-email`. Admin can manually verify: `PATCH /admin/users/{id}/verify-email`.
- **Token blacklist**: `utils/redis.py` blacklists JWTs on logout under key `token_blacklist:{sha256(token)}` with TTL = remaining validity. `get_redis()` returns a lazy-initialized singleton `redis.Redis` instance.
- **DB models**: Use `IDMixin` (UUID pk) + `TimestampMixin` (created_at/updated_at/deleted_at). Soft delete via `deleted_at` field. Services filter `deleted_at.is_(None)` when querying.
- **User model**: Has `email_verified: bool` (default False), `role: str` ("user" | "admin"), `status: str` ("active" | "inactive" | "banned"), `muted_until: datetime | None` (board masters and admins can mute users).
- **Post model**: Has `is_pinned`, `is_featured`, `status` (PostStatus enum: NORMAL/HIDDEN/DELETED), `published_at`, `comment_count`, `like_count`, `search_document` (tokenized text for ilike fallback), `search_vector` (TSVECTOR on PostgreSQL, Text fallback elsewhere). No `view_count` field.
- **Board model**: Has `slug: str`, `sort_order: int`, `post_count: int` (default 0).
- **Comment model**: Has `post_id`, `parent_comment_id`, `root_comment_id` (for nested threading), `like_count`, `reply_count`. Root comments have `root_comment_id` = NULL.
- **Announcement model**: title, content, is_published, starts_at/ends_at (nullable datetime), created_by (FK to users).
- **BoardMaster model**: board_id + user_id join table with partial unique index (deleted_at IS NULL). Soft delete. Re-adding a removed master restores the soft-deleted record.
- **Dependency injection**: Routers inject `db: Session` and `service` instances via `Depends()` from `deps/`. Services are stateless — `Session` is passed per-method.
- **Moderation**: `check_not_muted()` raises 403 if user's `muted_until` is in the future. `check_can_moderate_post()` and `check_can_moderate_board()` allow admin OR board master of the relevant board.
- **Search**: PostgreSQL uses `websearch_to_tsquery` + `ts_rank_cd` on `search_vector` (GIN index). SQLite fallback uses `ilike` on `search_document`. `utils/search.py` tokenizes with jieba (regex fallback if jieba unavailable). `SearchSort` enum: RELEVANCE/HOT/TIME. Hot score = `like_count * 2 + comment_count * 3`.
- **Password hashing**: `pwdlib[argon2]` via `utils/security.py` — argon2 is the specific algorithm, not just "recommended".

### Code Duplication

`create_access_token()` is defined in both `deps/auth.py` (public) and `services/auth_service.py` (private `_create_access_token`). If modifying JWT logic, update both.

## Frontend Architecture

Vue 3 + TypeScript + Vite + Element Plus. Uses unplugin-auto-import and unplugin-vue-components for Element Plus tree-shaking (no manual imports needed).

```
frontend/src/
  main.ts           → App entry (Vue, Pinia, Router, ElementPlus)
  App.vue           → Root component with AppHeader/AppFooter/router-view
  router/index.ts   → Routes with navigation guards (requiresAuth, requiresGuest, requiresAdmin)
  api/              → Axios API modules (client.ts, auth, users, posts, boards, comments, likes, notifications, admin, search, media)
  stores/           → Pinia stores (auth, posts, boards, notifications, ui)
  components/       → Reusable components organized by domain (admin/, board/, comment/, common/, notification/, post/)
  views/            → Page-level components (auth/, board/, post/, user/, notification/, admin/)
  types/            → TypeScript interfaces (user, post, comment, board, notification, media, api)
  utils/            → Helpers: storage.ts (token), format.ts, constants.ts, validation.ts, markdown.ts
```

### API Client (`frontend/src/api/client.ts`)

Axios instance with base URL from `VITE_API_BASE_URL` (empty in dev — proxy handles routing). Request interceptor attaches Bearer token. Response interceptor unwraps `ApiResponse.data` on success (2xx); on error, handles 401 (clears token), 429 (rate limit toast), 500 (server error toast).

### Router Guards (`frontend/src/router/index.ts`)

- `beforeEach`: sets document title, calls `authStore.restoreSession()` if token exists but no user loaded
- `requiresAuth`: redirects to `/login?redirect=...` if not authenticated
- `requiresGuest`: redirects to `/` if already authenticated
- `requiresAdmin`: redirects to `/` if not admin

### Auth Store (`frontend/src/stores/auth.ts`)

Manages `token` (synced to localStorage via `utils/storage.ts`), `currentUser`, `loading`. `login()` calls API → stores token → fetches profile. `restoreSession()` re-fetches profile on page refresh if token exists. `logout()` calls API → clears token and user.

### Key Frontend Patterns

- **API calls**: All API functions return the unwrapped data (interceptor strips `ApiResponse` envelope). Stores and views receive bare payloads.
- **Post store**: Manages `postList`, `currentPost`, `pagination`. `updateLikeCount(postId, delta)` and `updateCommentCount(postId, delta)` for optimistic UI.
- **Notification store**: Polls `getUnreadCount` every 30 seconds via `startPolling()` / `stopPolling()`.
- **Comment threading**: `CommentTree` renders root comments (page from `CommentWithReplies.replies`). `CommentItem` recurses via `children` prop.
- **Markdown rendering**: `utils/markdown.ts` uses `markdown-it` + KaTeX (math) + DOMPurify. Post editor uses `md-editor-v3`. Avatar cropping uses `cropperjs` in `AvatarCropDialog.vue` (1:1 aspect, 256x256 output).
- **Element Plus**: Components auto-imported. Icons from `@element-plus/icons-vue` imported explicitly.

### Frontend Config

- Dev: Vite proxies `/api/v1` → `http://localhost:8000` (configured in `vite.config.ts`)
- Production: `VITE_API_BASE_URL` in `.env.production` sets the API base URL. Currently empty — needs to be set for production deploys.
- Production Docker: `frontend/Dockerfile` multi-stage (node:22-alpine build → nginx:alpine serve). `nginx.conf` proxies `/api/v1/` to backend:8000 with `client_max_body_size 10M` + gzip.

## Test Infrastructure

Backend tests use **SQLite file-based** (one DB per test module) and **fakeredis**, so no Docker services needed.

- `conftest.py` autouse fixture swaps `app.utils.redis._redis` with a shared `fakeredis.FakeRedis(decode_responses=True)` singleton, flushed on teardown
- Each test file defines its own SQLite engine, `TestingSessionLocal`, `_setup_db` fixture (`Base.metadata.create_all` / `drop_all`), and `_override_get_db()` dependency override
- `app.dependency_overrides[get_db]` — injects test DB session
- `_make_mock_email_service()` — creates an `EmailService` with `send_verification_email` mocked (but real JWT token generation), injected via `app.dependency_overrides[get_email_service]`
- Sync tests use `TestClient`; async tests use `AsyncClient` + `pytest.mark.asyncio` (test_admin, test_search, test_announcements, test_board_master)
- `concurrency_utils.py` provides `race_requests()` helper (ThreadPoolExecutor + threading.Barrier) for concurrent request testing
- Performance tests benchmark post listing (<2s for 50 posts) and search (<3s across 50 posts)
- Stability tests cover rapid like/unlike cycles, long operation sequences, concurrent mixed reads/writes

## Media Storage Architecture

- `storage/base.py` — `StorageBackend` ABC with `put()`, `get()`, `delete()`, `url_for()` methods
- `storage/s3.py` — `S3StorageBackend` — boto3-based S3 implementation, lazy bucket creation
- `storage/memory.py` — `InMemoryStorageBackend` — dict-based impl for tests
- `storage/factory.py` — `get_storage_backend()` — lru_cache singleton, reads S3 settings from config

Upload flow: client `POST /media/upload` → `MediaService.upload()` validates MIME/size, SHA256 dedup per user → `StorageBackend.put()` → `MediaAsset` row → `MediaUploadResponse`. Download: `GET /media/{id}` streams raw binary (no ApiResponse wrapper). Info: `GET /media/{id}/info` returns metadata (ApiResponse-wrapped). Avatar: `PATCH /users/me/avatar` uploads + updates `user.avatar_media_id`.

Docker infrastructure: Garage (S3-compatible) v1.1.0 on ports 3900-3903. `garage.toml` at repo root. Garage binary inside container is `/garage` (not `garage`). Backend Dockerfile uses `uv:python3.14-bookworm`, runs `alembic upgrade head` before uvicorn.

## Key Config

`backend/app/config.py` reads from `.env`. Key defaults:

| Variable | Default | Purpose |
|----------|---------|---------|
| `DATABASE_URL` | `postgresql+psycopg2://bbs_user:bbs_password@localhost:5432/bbs` | Postgres connection |
| `REDIS_HOST` / `REDIS_PORT` / `REDIS_DB` | `localhost` / `6379` / `0` | Redis connection |
| `JWT_SECRET` | (auto-generated by `make setup-env`) | HS256 signing key |
| `JWT_ALGORITHM` | `HS256` | JWT algorithm |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | Access token TTL |
| `FRONTEND_BASE_URL` | `http://localhost:5173` | Verification emails + CORS |
| `BACKEND_BASE_URL` | `http://localhost:8000` | Backend self-URL |
| `SMTP_HOST` / `SMTP_PORT` | `localhost` / `1025` | Mailpit in dev |
| `SMTP_USER` / `SMTP_PASSWORD` / `SMTP_USE_TLS` | empty / empty / False | SMTP auth |
| `EMAIL_VERIFY_TOKEN_EXPIRE_MINUTES` | `1440` (24h) | Verification link TTL |
| `S3_ENDPOINT_URL` | `http://localhost:3900` | S3-compatible storage endpoint |
| `S3_BUCKET_NAME` | `bbs-media` | S3 bucket name |
| `UPLOAD_MAX_SIZE_MB` / `UPLOAD_MAX_PER_POST` | `5` / `20` | Upload limits |
| `UPLOAD_ALLOWED_MIME_TYPES` | `image/jpeg,image/png,image/gif,image/webp` | Allowed MIME types |

## Database Design

Full schema spec in `docs/DatabaseDesign.md`. Core tables: users, boards, posts, comments, post_likes, comment_likes, media_assets, post_attachments, notifications, announcements, board_masters. All PKs are UUID. Connection defaults: Postgres `localhost:5432` (db=bbs, user=bbs_user, pass=bbs_password), Redis `localhost:6379`.

## Git Conventions

- Branches: `feat/<subsystem>-<feature>-<date>`, `fix/`, `refactor/`, `docs/`
- Commits: `<type>(<scope>): <subject>` — types: feat, fix, refactor, docs, test, chore
- Flow: feature branch → develop (PR with review) → main (lead merges)
- Pre-commit hook runs lint-staged (black + ruff --fix on backend/**/*.py)

## API Conventions

RESTful under `/api/v1/`. PATCH for partial updates. HTTP status codes follow spec in `docs/DevelopmentSpecification.md` (200/201/204/400/401/403/404/409/422/429/500).