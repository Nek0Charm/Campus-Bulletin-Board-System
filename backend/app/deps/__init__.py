"""
deps 层负责依赖注入封装

被 app.routers 各路由模块通过 Depends 方式统一使用。

"""

from app.deps.auth import create_access_token
from app.deps.auth import decode_access_token
from app.deps.auth import get_current_user
from app.deps.auth import require_admin
from app.deps.db import get_db
from app.deps.services import get_auth_service
from app.deps.services import get_user_service

__all__ = [
    "get_db",
    "create_access_token",
    "decode_access_token",
    "get_current_user",
    "require_admin",
    "get_auth_service",
    "get_user_service",
]
