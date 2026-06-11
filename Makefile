.DEFAULT_GOAL := help

COMPOSE ?= docker compose
BACKEND_DIR ?= backend
FRONTEND_DIR ?= frontend
BACKEND_DEV_CMD ?= uv run uvicorn app.main:app --reload
FRONTEND_DEV_CMD ?= pnpm run dev

.PHONY: help deps-up deps-down deps-logs deps-ps deps-reset-db backend frontend dev format format-backend format-frontend lint lint-backend lint-frontend migration-new migrate migrate-rollback migrate-history init-garage setup-env test-e2e test-e2e-headed perftest-seed perftest-baseline perftest-load perftest-stress perftest-interface perftest-ui perftest-clean

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
	@echo "  make perftest-seed                # 创建性能测试用户数据（200 普通用户 + 1 管理员）"
	@echo "  make perftest-baseline            # 运行基准性能测试（50 用户，5 分钟）"
	@echo "  make perftest-load                # 运行负载性能测试（逐步增至 500 用户）"
	@echo "  make perftest-stress              # 运行压力性能测试（逐步增至 1000 用户）"
	@echo "  make perftest-interface           # 运行接口专项性能测试（各接口独立测 P95）"
	@echo "  make perftest-ui                  # 启动 Locust Web UI（端口 8089）"
	@echo "  make perftest-clean               # 清理性能测试报告文件"

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

perftest-seed:
	@cd $(BACKEND_DIR) && uv run python perftests/seed_data.py --num-users 200 --password PerfTest123!

perftest-baseline:
	@mkdir -p $(BACKEND_DIR)/perftests/reports
	@cd $(BACKEND_DIR) && uv run locust -f perftests/locustfile.py --headless \
	    -u 50 -r 10 -t 5m --host=http://localhost:8000 \
	    --csv=perftests/reports/baseline --html=perftests/reports/baseline.html

perftest-load:
	@mkdir -p $(BACKEND_DIR)/perftests/reports
	@cd $(BACKEND_DIR) && uv run locust -f perftests/locustfile.py --headless \
	    -u 500 -r 50 -t 15m --host=http://localhost:8000 \
	    --csv=perftests/reports/load --html=perftests/reports/load.html \
	    --step-load --step-users 50 --step-time 2m

perftest-stress:
	@mkdir -p $(BACKEND_DIR)/perftests/reports
	@cd $(BACKEND_DIR) && uv run locust -f perftests/locustfile.py --headless \
	    -u 1000 -r 100 -t 9m --host=http://localhost:8000 \
	    --csv=perftests/reports/stress --html=perftests/reports/stress.html \
	    --step-load --step-users 100 --step-time 1m

perftest-interface:
	@mkdir -p $(BACKEND_DIR)/perftests/reports
	@cd $(BACKEND_DIR) && uv run locust -f perftests/locustfile_interfaces.py --headless \
	    -u 50 -r 10 -t 3m --host=http://localhost:8000 \
	    --csv=perftests/reports/interface --html=perftests/reports/interface.html

perftest-ui:
	@cd $(BACKEND_DIR) && uv run locust -f perftests/locustfile.py --host=http://localhost:8000

perftest-clean:
	@rm -rf $(BACKEND_DIR)/perftests/reports/*.csv $(BACKEND_DIR)/perftests/reports/*.html $(BACKEND_DIR)/perftests/reports/*.log
