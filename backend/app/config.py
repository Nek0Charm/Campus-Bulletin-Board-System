"""
统一管理后端配置（项目元信息、数据库、Redis、JWT 等）。
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Campus BBS"
    VERSION: str = "0.1.0"
    API_PREFIX: str = "/api/v1"

    # PostgreSQL
    DATABASE_URL: str = "postgresql+psycopg2://bbs_user:bbs_password@localhost:5432/bbs"

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    # JWT
    JWT_SECRET: str = "SecretKeyMustBeAtLeast32BytesLongForSHA256"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Frontend
    FRONTEND_BASE_URL: str = "http://localhost:5173"

    # Email / SMTP (defaults point to Mailpit for dev)
    BACKEND_BASE_URL: str = "http://localhost:8000"
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 1025
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "noreply@campus-bbs.local"
    SMTP_USE_TLS: bool = False
    EMAIL_VERIFY_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


def get_settings() -> Settings:
    return Settings()
