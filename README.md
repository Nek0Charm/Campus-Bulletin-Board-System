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

## 工作流程
> 详见 docs/DevelopmentSpecification.md
```
# 1. 从 develop 创建功能分支
git checkout develop
git pull origin develop
git checkout -b feat/user-crud-0401

# 2. 开发并提交
git add .
git commit -m "feat(user): add user CRUD API"
git push origin feat/user-crud-0401

# 3. 合并到 develop（所有组员）
git checkout develop
git merge feat/user-crud-0401 --no-ff
git push origin develop

# 5. develop → main（组长协商后执行）
```

如何快速更改文档：
```bash
# 1. 在docs/xxx 分支提交修改
git checkout docs/readme-update-xxxx
git add README.md
git commit -m "docs: update README"
git push origin docs/readme-update-xxxx

# 2. 提交 PR 将 docs/xxx 合并到 develop （在github操作）
```

开发时需要同步其他人的更改：
```bash
# 1. 拉取远程仓库
git fetch origin

# 2. 切换到当前工作分支
git checkout feat/xxxx

# 3. 合并 develop 分支的更改
git merge origin/develop
```
