"""
services 层负责核心业务实现。

被 app.routers 调用（通常通过 deps.services 注入）。

"""

from app.services.auth_service import AuthService
from app.services.user_service import UserService
from app.services.post_service import PostService

__all__ = [
    "AuthService",
    "UserService",
    "PostService",
]
