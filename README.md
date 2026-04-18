# Campus Bulletin Board System

校园论坛项目，目标是提供用户注册、发帖、评论、点赞等基础社区能力。

## 技术栈

| 层 | 技术 |
| --- | --- |
| 前端 | TypeScript（React / Vue 待定），pnpm |
| 后端 | Python、FastAPI、SQLAlchemy、Pydantic、PyJWT、pwdlib |
| 数据与缓存 | PostgreSQL、Redis |
| 工程与质量 | Docker Compose、uv、black、ruff、pytest、Husky |

## 快速开始开发

1. 启动依赖服务（PostgreSQL + Redis）

```bash
make deps-up
```

2. 安装后端依赖

```bash
cd backend
uv sync
cd ..
```

3. 启动后端开发环境

```bash
make backend
```

4. 启动前端（前端代码初始化后）

```bash
make frontend
```

5. （可选）初始化 Git hooks

```bash
pnpm install
pnpm run prepare
```

## 常用命令

```bash
make dev         # 启动依赖服务，并提示前后端启动命令
make deps-logs   # 查看 PostgreSQL / Redis 日志
make deps-down   # 停止并清理依赖服务
pnpm run format  # 格式化 backend 代码（等效于在 backend/ 目录 uvx black .）
pnpm run lint    # backend 静态检查（等效于在 backend/ 目录 uvx ruff check .）
```

## 本地默认连接信息

- PostgreSQL: `localhost:5432`，数据库 `bbs`，用户 `bbs_user`，密码 `bbs_password`
- Redis: `localhost:6379`

> 当前仓库中的 `frontend/` 仅保留占位文件。
