from app.services.auth_service import AuthService
from app.services.user_service import UserService
from app.services.post_service import PostService
from app.services.board_service import BoardService
from app.services.email_service import EmailService
from app.services.notification_service import NotificationService
from app.services.like_service import LikeService
from app.services.comment_service import CommentService


def get_auth_service() -> AuthService:
    return AuthService()


def get_user_service() -> UserService:
    return UserService()


def get_post_service() -> PostService:
    return PostService()


def get_board_service() -> BoardService:
    return BoardService()


def get_email_service() -> EmailService:
    return EmailService()


def get_notification_service() -> NotificationService:
    return NotificationService()


def get_like_service() -> LikeService:
    return LikeService()


def get_comment_service() -> CommentService:
    return CommentService()


__all__ = [
    "get_auth_service",
    "get_user_service",
    "get_post_service",
    "get_board_service",
    "get_email_service",
    "get_notification_service",
    "get_like_service",
    "get_comment_service",
]
