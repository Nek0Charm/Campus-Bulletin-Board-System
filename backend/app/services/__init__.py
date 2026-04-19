"""
services 层负责核心业务实现。

被 app.routers 调用（通常通过 deps.services 注入）。

"""

from app.services.auth_service import AuthService

__all__ = [
    "AuthService",
]
