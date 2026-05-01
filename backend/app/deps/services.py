from app.services.auth_service import AuthService
from app.services.user_service import UserService


def get_auth_service() -> AuthService:
    return AuthService()


def get_user_service() -> UserService:
    return UserService()


__all__ = ["get_auth_service", "get_user_service"]
