"""
schemas 层定义请求/响应数据结构。

被 routers 层用作入参和出参模型。
与 services 层返回的数据结构保持一致。

"""

from app.schemas.auth import AuthUserData
from app.schemas.auth import LoginData
from app.schemas.auth import LoginRequest
from app.schemas.auth import LogoutData
from app.schemas.auth import RegisterData
from app.schemas.auth import RegisterRequest
from app.schemas.auth import ResetPasswordData
from app.schemas.auth import ResetPasswordRequest
from app.schemas.auth import VerifyEmailData
from app.schemas.auth import VerifyEmailRequest
from app.schemas.auth import ResendVerifyRequest
from app.schemas.user import AdminUserData
from app.schemas.user import UpdateProfileRequest
from app.schemas.user import UpdateUserStatusRequest
from app.schemas.user import UserProfileData
from app.schemas.user import UserPublicData
from app.schemas.post import PostCreate, PostUpdate, PostRead, PostListResponse
from app.schemas.post import PinToggleRequest, FeatureToggleRequest
from app.schemas.announcement import (
    AnnouncementCreate,
    AnnouncementRead,
    AnnouncementUpdate,
)
from app.schemas.board import BoardCreate, BoardRead, BoardUpdate
from app.schemas.admin import AdminStatsResponse
from app.schemas.notification import NotificationMarkAllReadResult
from app.schemas.notification import NotificationRead
from app.schemas.notification import NotificationUnreadCount

__all__ = [
    "RegisterRequest",
    "LoginRequest",
    "AuthUserData",
    "RegisterData",
    "LoginData",
    "LogoutData",
    "ResetPasswordRequest",
    "ResetPasswordData",
    "VerifyEmailRequest",
    "VerifyEmailData",
    "ResendVerifyRequest",
    "UserProfileData",
    "UpdateProfileRequest",
    "UserPublicData",
    "AdminUserData",
    "UpdateUserStatusRequest",
    "PostCreate",
    "PostUpdate",
    "PostRead",
    "PostListResponse",
    "PinToggleRequest",
    "FeatureToggleRequest",
    "BoardCreate",
    "BoardRead",
    "BoardUpdate",
    "AdminStatsResponse",
    "AnnouncementCreate",
    "AnnouncementRead",
    "AnnouncementUpdate",
    "NotificationRead",
    "NotificationUnreadCount",
    "NotificationMarkAllReadResult",
]
