from pydantic import BaseModel
from pydantic import EmailStr
from pydantic import Field


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=32)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    nickname: str | None = Field(default=None, min_length=1, max_length=64)


class LoginRequest(BaseModel):
    account: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=1, max_length=128)


class AuthUserData(BaseModel):
    id: str
    username: str
    email: str
    nickname: str | None = None
    role: str
    status: str | None = None


class RegisterData(BaseModel):
    user: AuthUserData


class LoginData(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    user: AuthUserData


class LogoutData(BaseModel):
    message: str


class ResetPasswordRequest(BaseModel):
    old_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


class ResetPasswordData(BaseModel):
    message: str
