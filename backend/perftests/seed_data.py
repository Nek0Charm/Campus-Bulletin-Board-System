"""
性能测试数据种子脚本 — 直接在 PostgreSQL 中创建已验证的测试用户。

用法:
    uv run python perftests/seed_data.py
    uv run python perftests/seed_data.py --num-users 200 --password PerfTest123!
    uv run python perftests/seed_data.py --num-users 50 --admin-count 2

注意事项:
    - 需要 PostgreSQL 服务已启动且数据库迁移已完成
    - 增量创建：跳过已存在的 perftest 用户
    - 创建的用户均设为 email_verified=True, status="active"
    - 输出 user_pool.json 供 Locust 任务使用
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import SessionLocal
from app.models.board import Board
from app.models.post import Post
from app.models.user import User
from app.utils.security import hash_password

USER_POOL_PATH = Path(__file__).resolve().parent / "user_pool.json"

PERFTEST_USERNAME_PREFIX = "perftest_"
PERFTEST_EMAIL_DOMAIN = "campus.edu.cn"
PERFTEST_ADMIN_PREFIX = "perftest_admin_"


def check_base_data(db) -> bool:
    """检查是否已有基础测试数据（板块和帖子）。"""
    board_count = db.query(Board).filter(Board.deleted_at.is_(None)).count()
    post_count = db.query(Post).filter(Post.deleted_at.is_(None)).count()
    if board_count == 0 or post_count == 0:
        print("⚠️  数据库中板块或帖子为空，建议先运行:")
        print("    cd backend && uv run python scripts/import_test_data.py")
        print()
        return False
    print(f"✅ 基础数据检查通过: {board_count} 个板块, {post_count} 个帖子")
    return True


def create_regular_users(db, num_users: int, password: str) -> list[dict]:
    """创建普通测试用户，返回凭据列表。"""
    existing = {
        r[0]
        for r in db.query(User.username)
        .filter(
            User.deleted_at.is_(None),
            User.username.like(f"{PERFTEST_USERNAME_PREFIX}%"),
        )
        .all()
    }
    credentials = []
    created = 0
    skipped = 0

    for i in range(1, num_users + 1):
        username = f"{PERFTEST_USERNAME_PREFIX}{i:03d}"
        email = f"{PERFTEST_USERNAME_PREFIX}{i:03d}@{PERFTEST_EMAIL_DOMAIN}"

        if username in existing:
            skipped += 1
            # 已存在但仍加入凭据池（假设密码相同）
            credentials.append({"username": username, "password": password})
            continue

        user = User(
            username=username,
            email=email,
            password_hash=hash_password(password),
            nickname=f"测试用户{i}",
            role="user",
            status="active",
            email_verified=True,
        )
        db.add(user)
        credentials.append({"username": username, "password": password})
        created += 1

    db.flush()
    print(
        f"  创建 {created} 个普通用户"
        + (f" (跳过 {skipped} 个已存在)" if skipped else "")
    )
    return credentials


def create_admin_users(db, admin_count: int, password: str) -> list[dict]:
    """创建管理员测试用户，返回凭据列表。"""
    existing = {
        r[0]
        for r in db.query(User.username)
        .filter(
            User.deleted_at.is_(None),
            User.username.like(f"{PERFTEST_ADMIN_PREFIX}%"),
        )
        .all()
    }
    credentials = []
    created = 0
    skipped = 0

    for i in range(1, admin_count + 1):
        username = f"{PERFTEST_ADMIN_PREFIX}{i:03d}"
        email = f"{PERFTEST_ADMIN_PREFIX}{i:03d}@{PERFTEST_EMAIL_DOMAIN}"

        if username in existing:
            skipped += 1
            credentials.append({"username": username, "password": password})
            continue

        user = User(
            username=username,
            email=email,
            password_hash=hash_password(password),
            nickname=f"测试管理员{i}",
            role="admin",
            status="active",
            email_verified=True,
        )
        db.add(user)
        credentials.append({"username": username, "password": password})
        created += 1

    db.flush()
    print(
        f"  创建 {created} 个管理员用户"
        + (f" (跳过 {skipped} 个已存在)" if skipped else "")
    )
    return credentials


def write_user_pool(
    regular_credentials: list[dict], admin_credentials: list[dict]
) -> None:
    """将用户凭据池写入 JSON 文件供 Locust 使用。"""
    pool = {
        "regular_users": regular_credentials,
        "admin_users": admin_credentials,
    }
    USER_POOL_PATH.write_text(json.dumps(pool, indent=2, ensure_ascii=False))
    print(f"✅ 用户凭据池已写入: {USER_POOL_PATH}")
    print(f"   普通用户: {len(regular_credentials)} 个")
    print(f"   管理员:   {len(admin_credentials)} 个")


def main():
    parser = argparse.ArgumentParser(
        description="性能测试数据种子脚本 — 创建已验证的测试用户"
    )
    parser.add_argument(
        "--num-users",
        type=int,
        default=200,
        help="创建的普通用户数量 (默认: 200)",
    )
    parser.add_argument(
        "--admin-count",
        type=int,
        default=1,
        help="创建的管理员用户数量 (默认: 1)",
    )
    parser.add_argument(
        "--password",
        type=str,
        default="PerfTest123!",
        help="所有测试用户的统一密码 (默认: PerfTest123!)",
    )
    args = parser.parse_args()

    print("=" * 50)
    print("校园论坛性能测试 — 用户数据种子脚本")
    print("=" * 50)
    print()

    with SessionLocal() as db:
        try:
            # 检查基础数据
            has_base_data = check_base_data(db)
            if not has_base_data:
                print("继续创建用户（但后续压测可能缺少帖子/板块数据）...")
                print()

            # 创建普通用户
            print("[1/2] 创建普通测试用户...")
            regular_credentials = create_regular_users(
                db, args.num_users, args.password
            )
            print()

            # 创建管理员用户
            print("[2/2] 创建管理员测试用户...")
            admin_credentials = create_admin_users(db, args.admin_count, args.password)
            print()

            db.commit()

            # 写入凭据池
            write_user_pool(regular_credentials, admin_credentials)
            print()

            print("=" * 50)
            print("用户数据种子完成！")
            print("=" * 50)
            print()
            print("示例登录账号:")
            if regular_credentials:
                print(
                    f"  普通用户: {regular_credentials[0]['username']} / {regular_credentials[0]['password']}"
                )
            if admin_credentials:
                print(
                    f"  管理员:   {admin_credentials[0]['username']} / {admin_credentials[0]['password']}"
                )
            print()
            print("下一步:")
            print("  1. 确保后端服务运行: make backend")
            print("  2. 启动 Locust:     make perftest-ui")
            print("  3. 或运行基准测试:  make perftest-baseline")

        except Exception as e:
            db.rollback()
            print(f"\n❌ 创建失败: {e}")
            raise


if __name__ == "__main__":
    main()
