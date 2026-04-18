from sqlalchemy import create_engine
from sqlalchemy import text
from sqlalchemy.orm import Session
from redis import StrictRedis

"""
测试Redis 和 PostgresSQL 连接是否正常
"""
redis = StrictRedis(host="localhost", port=6379, db=0, decode_responses=True)
redis.set("test_key", "Hello, Redis!")
print(redis.get("test_key"))

engine = create_engine("postgresql+psycopg2://bbs_user:bbs_password@localhost:5432/bbs")

stmt = text("SELECT EXISTS(SELECT 1 FROM pg_tables WHERE tablename = 'some_table')")

with Session(engine) as session:
    result = session.execute(stmt)
    if not result.scalar():
        stmt = text("CREATE TABLE some_table (x int, y int)")

        with Session(engine) as session:
            session.execute(stmt)
            session.commit()

stmt = text("INSERT INTO some_table (x, y) VALUES (:x, :y)")

with Session(engine) as session:
    session.execute(stmt, [{"x": 1, "y": 2}, {"x": 3, "y": 4}])
    session.commit()

stmt = text("SELECT x, y FROM some_table")

with Session(engine) as session:
    result = session.execute(stmt)
    for row in result:
        print(f"x: {row.x}, y: {row.y}")
