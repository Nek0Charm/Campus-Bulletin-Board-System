.DEFAULT_GOAL := help

COMPOSE ?= docker compose
BACKEND_DIR ?= backend
FRONTEND_DIR ?= frontend
BACKEND_DEV_CMD ?= uv run uvicorn app.main:app --reload
FRONTEND_DEV_CMD ?= pnpm run dev

.PHONY: help deps-up deps-down deps-logs deps-ps deps-reset-db backend frontend dev format format-backend format-frontend lint lint-backend lint-frontend migration-new migrate migrate-rollback migrate-history init-garage setup-env test-e2e test-e2e-headed

help:
	@echo "可用命令："
	@echo "  make deps-up                      # 启动 PostgreSQL 和 Redis"
	@echo "  make deps-down                    # 停止并清理依赖服务"
	@echo "  make deps-logs                    # 查看依赖服务日志"
	@echo "  make deps-reset-db                # 重置 PostgreSQL 和 Garage 数据卷并重建服务"
	@echo "  make backend                      # 启动后端（默认: uv run uvicorn app.main:app --reload）"
	@echo "  make frontend                     # 启动前端（默认: pnpm run dev）"
	@echo "  make dev                          # 先启动依赖服务，再给出前后端启动提示"
	@echo "  make format                       # 格式化前后端代码（black + prettier）"
	@echo "  make format-backend               # 格式化后端代码（black）"
	@echo "  make format-frontend              # 格式化前端代码（prettier）"
	@echo "  make lint                         # 静态检查前后端代码（ruff + oxlint + eslint）"
	@echo "  make lint-backend                 # 静态检查后端代码（ruff）"
	@echo "  make lint-frontend                # 静态检查前端代码（oxlint + eslint）"
	@echo "  make migration-new msg=\"...\"       # 自动生成新迁移"
	@echo "  make migrate                      # 执行所有待处理的迁移"
	@echo "  make migrate-rollback             # 回滚最近一次迁移"
	@echo "  make migrate-history              # 查看迁移历史"
	@echo "  make init-garage                  # 初始化 Garage S3 存储（首次启动后运行）"
	@echo "  make test-e2e                     # 运行 Playwright e2e 测试（需要后端和前端已启动）"
	@echo "  make test-e2e-headed              # 运行 Playwright e2e 测试（有头模式）"

setup-env:
	@if [ ! -f .env ]; then cp .env.example .env; echo "已创建 .env"; fi
	@if ! grep -q '^GARAGE_RPC_SECRET=.' .env; then \
		SECRET=$$(openssl rand -hex 32) && \
		sed -i "s/^GARAGE_RPC_SECRET=.*/GARAGE_RPC_SECRET=$$SECRET/" .env 2>/dev/null || \
		echo "GARAGE_RPC_SECRET=$$SECRET" >> .env; \
		echo "已生成 GARAGE_RPC_SECRET"; \
	fi
	@if ! grep -q '^JWT_SECRET=.' .env || grep -q '^JWT_SECRET=change-me' .env; then \
		SECRET=$$(openssl rand -hex 32) && \
		sed -i "s/^JWT_SECRET=.*/JWT_SECRET=$$SECRET/" .env; \
		echo "已生成 JWT_SECRET"; \
	fi

deps-up: setup-env
	@$(COMPOSE) up -d postgres redis mailpit garage

init-garage:
	@echo "初始化 Garage S3 存储..."
	@docker exec bbs-garage /garage layout assign -z dc1 -c 1G $$(docker exec bbs-garage /garage node id 2>/dev/null | awk '{print $$1}') 2>/dev/null || true
	@docker exec bbs-garage /garage layout apply --version 1 2>/dev/null || true
	@if docker exec bbs-garage /garage key info bbs 2>/dev/null | grep -q 'Key name'; then \
		echo "Key 'bbs' 已存在，跳过创建"; \
	else \
		docker exec bbs-garage /garage key create bbs; \
		echo "已创建 Key 'bbs'"; \
	fi
	@if docker exec bbs-garage /garage bucket info bbs-media 2>/dev/null | grep -q 'Global aliases'; then \
		echo "Bucket 'bbs-media' 已存在，跳过创建"; \
	else \
		docker exec bbs-garage /garage bucket create bbs-media; \
		echo "已创建 Bucket 'bbs-media'"; \
	fi
	@docker exec bbs-garage /garage bucket allow --read --write bbs-media --key bbs 2>/dev/null || true
	@KEY_ID=$$(docker exec bbs-garage /garage key info bbs --show-secret 2>/dev/null | grep 'Key ID' | awk '{print $$3}') && \
	SECRET_KEY=$$(docker exec bbs-garage /garage key info bbs --show-secret 2>/dev/null | grep 'Secret key' | awk '{print $$3}') && \
	if [ -f .env ]; then \
		sed -i "/^S3_ACCESS_KEY_ID=/c\S3_ACCESS_KEY_ID=$$KEY_ID" .env 2>/dev/null || echo "S3_ACCESS_KEY_ID=$$KEY_ID" >> .env; \
		sed -i "/^S3_SECRET_ACCESS_KEY=/c\S3_SECRET_ACCESS_KEY=$$SECRET_KEY" .env 2>/dev/null || echo "S3_SECRET_ACCESS_KEY=$$SECRET_KEY" >> .env; \
	fi && \
	echo "Garage 初始化完成！密钥已写入 .env：" && \
	echo "  S3_ACCESS_KEY_ID=$$KEY_ID" && \
	echo "  S3_SECRET_ACCESS_KEY=$$SECRET_KEY"

deps-down:
	@$(COMPOSE) down

deps-logs:
	@$(COMPOSE) logs -f postgres redis mailpit

deps-ps:
	@$(COMPOSE) ps

deps-reset-db:
	@$(COMPOSE) down postgres garage
	@docker volume rm bbs_postgres_data bbs_garage_data bbs_garage_meta
	@$(COMPOSE) up -d postgres garage
	@$(COMPOSE) ps postgres garage

backend:
	@cd $(BACKEND_DIR) && $(BACKEND_DEV_CMD)

frontend:
	@cd $(FRONTEND_DIR) && $(FRONTEND_DEV_CMD)

dev: deps-up
	@echo "依赖服务已启动。请在两个终端分别执行："
	@echo "  make backend"
	@echo "  make frontend"

format: format-backend format-frontend

format-backend:
	@cd $(BACKEND_DIR) && uvx black .

format-frontend:
	@cd $(FRONTEND_DIR) && pnpm run format

lint: lint-backend lint-frontend

lint-backend:
	@cd $(BACKEND_DIR) && uvx ruff check .

lint-frontend:
	@cd $(FRONTEND_DIR) && pnpm run lint

migration-new:
	@cd $(BACKEND_DIR) && uv run alembic revision --autogenerate -m "$(msg)"

migrate:
	@cd $(BACKEND_DIR) && uv run alembic upgrade head

migrate-rollback:
	@cd $(BACKEND_DIR) && uv run alembic downgrade -1

migrate-history:
	@cd $(BACKEND_DIR) && uv run alembic history

test-e2e:
	@cd $(FRONTEND_DIR) && NO_PROXY=localhost,127.0.0.1 no_proxy=localhost,127.0.0.1 pnpm run test:e2e

test-e2e-headed:
	@cd $(FRONTEND_DIR) && NO_PROXY=localhost,127.0.0.1 no_proxy=localhost,127.0.0.1 pnpm run test:e2e:headed
