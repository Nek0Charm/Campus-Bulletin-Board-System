from app.services.auth_service import AuthService
from app.services.user_service import UserService
from app.services.post_service import PostService
from app.services.board_service import BoardService


def get_auth_service() -> AuthService:
    return AuthService()


def get_user_service() -> UserService:
    return UserService()


def get_post_service() -> PostService:
    return PostService()


def get_board_service() -> BoardService:
    return BoardService()


__all__ = [
    "get_auth_service",
    "get_user_service",
    "get_post_service",
    "get_board_service",
]
