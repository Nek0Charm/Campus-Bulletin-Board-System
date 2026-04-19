.DEFAULT_GOAL := help

COMPOSE ?= docker compose
BACKEND_DIR ?= backend
FRONTEND_DIR ?= frontend
BACKEND_DEV_CMD ?= uv run uvicorn app.main:app --reload
FRONTEND_DEV_CMD ?= pnpm run dev

.PHONY: help deps-up deps-down deps-logs deps-ps deps-reset-db backend frontend dev format lint

help:
	@echo "可用命令："
	@echo "  make deps-up                      # 启动 PostgreSQL 和 Redis"
	@echo "  make deps-down                    # 停止并清理依赖服务"
	@echo "  make deps-logs                    # 查看依赖服务日志"
	@echo "  make deps-reset-db                # 重置 PostgreSQL 数据卷并重建数据库服务"
	@echo "  make backend                      # 启动后端（默认: uv run uvicorn app.main:app --reload）"
	@echo "  make frontend                     # 启动前端（默认: pnpm run dev）"
	@echo "  make dev                          # 先启动依赖服务，再给出前后端启动提示"

deps-up:
	@$(COMPOSE) up -d postgres redis

deps-down:
	@$(COMPOSE) down

deps-logs:
	@$(COMPOSE) logs -f postgres redis

deps-ps:
	@$(COMPOSE) ps

deps-reset-db:
	@$(COMPOSE) down postgres
	@docker volume rm bbs_postgres_data
	@$(COMPOSE) up -d postgres
	@$(COMPOSE) ps postgres

backend:
	@cd $(BACKEND_DIR) && $(BACKEND_DEV_CMD)

frontend:
	@cd $(FRONTEND_DIR) && $(FRONTEND_DEV_CMD)

dev: deps-up
	@echo "依赖服务已启动。请在两个终端分别执行："
	@echo "  make backend"
	@echo "  make frontend"
 
format:
	@cd $(BACKEND_DIR) && uvx black .
 
lint:
	@cd $(BACKEND_DIR) && uvx ruff check .
