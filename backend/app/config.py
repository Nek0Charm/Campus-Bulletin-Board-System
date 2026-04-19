"""
模块职责：
- 统一管理后端配置项（项目元信息、数据库、Redis、JWT 等）。

关联模块：
- 被 app.main、app.database、app.deps.auth、app.services.auth_service 等模块读取。
- 配置来源于环境变量与 .env 文件，通过 BaseSettings 自动解析。

新增功能开发：
1. 新增配置字段时优先补充默认值与类型声明，避免运行期隐式类型错误。
2. 需要外部可配置时，确保字段名与环境变量约定一致。
3. 若是安全相关配置（密钥、过期时间），同步检查 auth 相关流程是否需要联动调整。
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
    JWT_SECRET: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


def get_settings() -> Settings:
    return Settings()
