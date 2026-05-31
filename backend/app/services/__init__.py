"""
services 层负责核心业务实现。

被 app.routers 调用（通常通过 deps.services 注入）。

"""

from app.services.auth_service import AuthService
from app.services.user_service import UserService
from app.services.post_service import PostService
from app.services.board_service import BoardService
from app.services.email_service import EmailService
from app.services.notification_service import NotificationService
from app.services.announcement_service import AnnouncementService

__all__ = [
    "AuthService",
    "UserService",
    "PostService",
    "BoardService",
    "EmailService",
    "NotificationService",
    "AnnouncementService",
]
