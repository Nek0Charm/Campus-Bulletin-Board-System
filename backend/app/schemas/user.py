from pydantic import BaseModel
from pydantic import Field


class UpdateProfileRequest(BaseModel):
    nickname: str | None = Field(default=None, min_length=1, max_length=64)
    avatar_url: str | None = Field(default=None, max_length=1024)


class UserProfileData(BaseModel):
    id: str
    username: str
    email: str
    nickname: str | None = None
    avatar_url: str | None = None
    role: str
    status: str
    created_at: str
    updated_at: str


class UserPublicData(BaseModel):
    id: str
    username: str
    nickname: str | None = None
    avatar_url: str | None = None
    role: str


class UpdateUserStatusRequest(BaseModel):
    status: str = Field(pattern=r"^(active|inactive|banned)$")


class AdminUserData(BaseModel):
    id: str
    username: str
    email: str
    nickname: str | None = None
    avatar_url: str | None = None
    role: str
    status: str
    last_login_at: str | None = None
    created_at: str
