"""
创建 SQLAlchemy engine 与 Session 工厂。
app.deps.db 复用本模块的 get_db。
路由层经依赖注入拿到 Session 后，将其传入 services。
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import get_settings
from app.models import Base

settings = get_settings()

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


"""
拿到 db: Session 后
查询：db.query(Model).filter(...).first()
新增：db.add(instance); db.commit(); 
更新：查询到实例后修改属性，db.commit()
删除：db.delete(instance); db.commit()

https://docs.sqlalchemy.org.cn/en/20/orm/session_basics.html
"""


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
