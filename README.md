# Campus Bulletin Board System

校园论坛项目，提供用户注册、发帖、评论、点赞、通知等基础社区功能。

## 技术栈

| 层 | 技术 |
| --- | --- |
| 前端 | Vue 3 + TypeScript + Element Plus + Pinia + Vite，pnpm |
| 后端 | Python >=3.14、FastAPI、SQLAlchemy、Pydantic、PyJWT、pwdlib |
| 数据与缓存 | PostgreSQL、Redis |
| 邮件 | Mailpit（开发环境 SMTP 拦截 + Web 界面） |
| 工程与质量 | Docker Compose、uv、black、ruff、pytest、Husky |

## 快速开始

### 1. 启动依赖服务（PostgreSQL + Redis + Mailpit）

```bash
make deps-up
```

Mailpit Web 界面：`http://localhost:8025`（查看开发环境发送的验证邮件）。

### 2. 安装后端依赖并启动

```bash
cd backend
uv sync
cd ..
make backend
```

后端 API 文档：`http://localhost:8000/docs`

### 3. 安装前端依赖并启动

```bash
cd frontend
pnpm install
cd ..
make frontend
```

前端页面：`http://localhost:5173`

### 4. （可选）安装 Git hooks

```bash
pnpm install
pnpm run prepare
```

## 常用命令

```bash
make dev                 # 启动依赖服务，并提示前后端启动命令
make deps-down           # 停止依赖服务
make deps-logs           # 查看依赖服务日志
make deps-reset-db       # 重置数据库（清空所有数据）

make format              # 格式化前后端代码
make lint                # 静态检查前后端代码

make migration-new msg="描述"   # 自动生成数据库迁移
make migrate                   # 执行待处理的迁移
make migrate-rollback          # 回滚最近一次迁移
make migrate-history           # 查看迁移历史
```

### 单独运行

```bash
# 后端
cd backend && uvx ruff check .     # 后端静态检查
cd backend && uvx black .          # 后端格式化
cd backend && uv run pytest        # 运行后端测试
cd backend && uv run pytest -k "test_login"  # 按名称运行单个测试

# 前端
cd frontend && pnpm run lint       # 前端静态检查
cd frontend && pnpm run format     # 前端格式化
cd frontend && pnpm run test:unit  # 前端单元测试 (Vitest)
cd frontend && pnpm run build      # 类型检查 + 生产构建
```

## 本地默认连接信息

- PostgreSQL: `localhost:5432`，数据库 `bbs`，用户 `bbs_user`，密码 `bbs_password`
- Redis: `localhost:6379`
- SMTP: `localhost:1025`（Mailpit，Web 界面 `localhost:8025`）

## 项目结构

```
bbs/
├── backend/
│   ├── app/
│   │   ├── config.py          # 配置（读取 .env）
│   │   ├── database.py        # 数据库引擎、init_db、get_db
│   │   ├── main.py            # FastAPI 入口、路由注册
│   │   ├── models/            # SQLAlchemy ORM 模型
│   │   ├── schemas/           # Pydantic 请求/响应 Schema
│   │   ├── routers/           # API 路由（auth, users, posts, boards, comments, likes, notifications, admin）
│   │   ├── services/          # 业务逻辑层
│   │   ├── deps/              # FastAPI 依赖注入（auth, db, services）
│   │   └── utils/             # 工具（密码哈希, Redis）
│   ├── migrations/            # Alembic 数据库迁移
│   └── tests/                 # pytest 测试
├── frontend/
│   └── src/
│       ├── api/               # Axios API 模块
│       ├── stores/            # Pinia 状态管理
│       ├── router/            # Vue Router 路由配置
│       ├── components/        # 可复用组件
│       ├── views/             # 页面组件
│       ├── types/             # TypeScript 类型定义
│       └── utils/             # 工具函数
├── docs/                      # 设计文档
└── docker-compose.yml
```

## 工作流程

> 详见 docs/DevelopmentSpecification.md

```bash
# 1. 从 develop 创建功能分支
git checkout develop
git pull origin develop
git checkout -b feat/user-crud-0401

# 2. 开发并提交
git add .
git commit -m "feat(user): add user CRUD API"
git push origin feat/user-crud-0401

# 3. 合并到 develop
git checkout develop
git merge feat/user-crud-0401 --no-ff
git push origin develop

# 4. develop → main（组长协商后执行）
```

同步其他人的更改：

```bash
git fetch origin
git checkout feat/xxxx
git merge origin/develop
```
