"""
将指定用户的 role 设置为 admin。

用法:
    uv run python scripts/set_admin_role.py --username <username>
    uv run python scripts/set_admin_role.py --email <email>
    uv run python scripts/set_admin_role.py --username <username> --email <email>
"""

import argparse
import sys
from pathlib import Path

# 确保 backend/ 目录在 sys.path 中，以便 import app
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import SessionLocal
from app.models.user import User


def set_admin(username: str | None = None, email: str | None = None) -> None:
    if not username and not email:
        print("错误：请提供 --username 或 --email")
        sys.exit(1)

    with SessionLocal() as db:
        query = db.query(User).filter(User.deleted_at.is_(None))

        if username and email:
            from sqlalchemy import or_

            query = query.filter(or_(User.username == username, User.email == email))
        elif username:
            query = query.filter(User.username == username)
        else:
            query = query.filter(User.email == email)

        user = query.first()

        if not user:
            print("错误：未找到匹配的用户")
            sys.exit(1)

        if user.role == "admin":
            print(
                f"用户 {user.username} (email: {user.email}) 已经是 admin，无需修改。"
            )
            return

        user.role = "admin"
        db.commit()
        print(f"已将用户 {user.username} (email: {user.email}) 的角色更新为 admin。")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="将用户角色设为 admin")
    parser.add_argument("--username", type=str, help="用户名")
    parser.add_argument("--email", type=str, help="邮箱")
    args = parser.parse_args()

    set_admin(username=args.username, email=args.email)
