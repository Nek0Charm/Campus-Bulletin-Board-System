# Backend 开发与协作规范

## 1. 启动与常用命令

在仓库根目录执行：

```bash
make deps-up
make backend
```

后端启动命令为：

```bash
cd backend && uv run uvicorn app.main:app --reload
```

## 2. 后端目录结构

```text
backend/
├─ app/
│  ├─ main.py        # FastAPI 应用入口与路由注册
│  ├─ config.py      # 全局配置（BaseSettings）
│  ├─ database.py    # DB engine/session
│  ├─ deps/          # 依赖注入
│  ├─ routers/       # 路由层
│  ├─ services/      # 业务逻辑层
│  ├─ models/        # SQLAlchemy ORM 模型
│  ├─ schemas/       # Pydantic 请求/响应模型
│  └─ utils/         # 通用工具
├─ tests/            # 测试目录
└─ pyproject.toml    # Python 项目配置
```

## 3. 依赖注入

- `app/deps/db.py`：数据库依赖。
- `app/deps/auth.py`：认证依赖。
- `app/deps/services.py`：service provider。

## 4. 新功能开发模板

以新增一个模块为例（例如 `posts`）：

1. `routers/posts.py` 增加接口定义。
2. `services/post_service.py` 增加方法签名与实现。
3. `deps/services.py` 增加 service provider。
4. `schemas/` 增加请求/响应模型。
5. `models/` 补充或调整 ORM 模型。
6. `tests/` 增加路由测试与 service 测试。