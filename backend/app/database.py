"""
模块职责：
- 创建 SQLAlchemy engine 与 Session 工厂，并提供请求级数据库会话依赖。

关联模块：
- app.deps.db 直接复用本模块的 get_db。
- 路由层经依赖注入拿到 Session 后，将其传入 services 执行业务与持久化。

新增功能开发：
1. 调整连接池、数据库驱动或引擎参数时，统一在本模块处理。
2. 新增会话生命周期策略（如只读会话）时，优先扩展依赖函数而非在路由层分散实现。
3. 保持 get_db 的 yield/finally 结构，确保异常场景下连接也能正确释放。
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import get_settings

settings = get_settings()

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
