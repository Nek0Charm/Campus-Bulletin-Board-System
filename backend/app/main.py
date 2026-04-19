"""
FastAPI 应用入口，负责创建 app 实例并注册路由。

从 app.config 读取项目基础配置。
聚合 app.routers 下各路由模块，对外暴露统一 API 服务。

运行 uv run uvicorn app.main:app --reload 启动后，
访问 http://localhost:8000/docs 可查看自动生成的 API 文档。

"""

from fastapi import FastAPI

from app.config import get_settings
from app.routers import admin
from app.routers import auth
from app.routers import boards
from app.routers import comments
from app.routers import likes
from app.routers import notifications
from app.routers import posts
from app.routers import users

settings = get_settings()

app = FastAPI(title=settings.PROJECT_NAME, version=settings.VERSION)

app.include_router(auth.router, prefix=settings.API_PREFIX)
app.include_router(users.router, prefix=settings.API_PREFIX)
app.include_router(boards.router, prefix=settings.API_PREFIX)
app.include_router(posts.router, prefix=settings.API_PREFIX)
app.include_router(comments.router, prefix=settings.API_PREFIX)
app.include_router(likes.router, prefix=settings.API_PREFIX)
app.include_router(notifications.router, prefix=settings.API_PREFIX)
app.include_router(admin.router, prefix=settings.API_PREFIX)


@app.get("/health")
async def health_check():
    return {"status": "ok"}
