from functools import lru_cache

from app.services.auth_service import AuthService
from app.services.user_service import UserService
from app.services.post_service import PostService
from app.services.board_service import BoardService
from app.services.email_service import EmailService
from app.services.notification_service import NotificationService
from app.services.like_service import LikeService
from app.services.comment_service import CommentService
from app.services.media_service import MediaService
from app.services.board_master_service import BoardMasterService
from app.services.search_service import SearchService
from app.storage.factory import get_storage_backend
from app.services.announcement_service import AnnouncementService


def get_auth_service() -> AuthService:
    return AuthService()


def get_user_service() -> UserService:
    return UserService()


def get_post_service() -> PostService:
    return PostService()


def get_search_service() -> SearchService:
    return SearchService()


def get_board_service() -> BoardService:
    return BoardService()


def get_email_service() -> EmailService:
    return EmailService()


def get_notification_service() -> NotificationService:
    return NotificationService()


def get_like_service() -> LikeService:
    return LikeService(notification_service=NotificationService())


def get_comment_service() -> CommentService:
    return CommentService(notification_service=NotificationService())


@lru_cache
def get_media_service() -> MediaService:
    storage = get_storage_backend()
    return MediaService(storage=storage)


def get_board_master_service() -> BoardMasterService:
    return BoardMasterService()


def get_announcement_service() -> AnnouncementService:
    return AnnouncementService()


__all__ = [
    "get_auth_service",
    "get_user_service",
    "get_post_service",
    "get_search_service",
    "get_board_service",
    "get_email_service",
    "get_notification_service",
    "get_like_service",
    "get_comment_service",
    "get_media_service",
    "get_board_master_service",
    "get_announcement_service",
]
