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
cd backend && uv run pytest
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
- **Auth flow**: JWT (HS256) via PyJWT. `deps/auth.py` provides `create_access_token`, `decode_access_token`, `get_current_user`, `require_admin` as FastAPI dependencies. OAuth2PasswordBearer tokenUrl is `/api/v1/auth/login`.
- **DB models**: Use `IDMixin` (UUID pk) + `TimestampMixin` (created_at/updated_at/deleted_at) from `models/base.py`. Soft delete via `deleted_at` field.
- **Dependency injection**: Routers inject `db: Session` and `service` instances via `Depends()` from `deps/`.

### Database Design

Full schema spec in `docs/DatabaseDesign.md`. Core tables: users, boards, posts, comments, post_likes, comment_likes, media_assets, post_attachments, notifications. All PKs are UUID with `gen_random_uuid()`. Connection defaults: Postgres `localhost:5432` (db=bbs, user=bbs_user, pass=bbs_password), Redis `localhost:6379`.

## Git Conventions

- Branches: `feat/<subsystem>-<feature>-<date>`, `fix/`, `refactor/`, `docs/`
- Commits: `<type>(<scope>): <subject>` — types: feat, fix, refactor, docs, test, chore
- Flow: feature branch → develop (PR with review) → main (lead merges)
- Pre-commit hook runs lint-staged (black + ruff --fix on backend/**/*.py)

## API Conventions

RESTful under `/api/v1/`. PATCH for partial updates. HTTP status codes follow spec in `docs/DevelopmentSpecification.md` (200/201/204/400/401/403/404/409/422/429/500).