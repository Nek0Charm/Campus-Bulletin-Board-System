from app.services.auth_service import AuthService
from app.services.user_service import UserService
from app.services.post_service import PostService


def get_auth_service() -> AuthService:
    return AuthService()


def get_user_service() -> UserService:
    return UserService()


def get_post_service() -> PostService:
    return PostService()


__all__ = ["get_auth_service", "get_user_service", "get_post_service"]
