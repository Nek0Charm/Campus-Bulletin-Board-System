"""
同步数据库中的聚合计数字段（post_count, comment_count, like_count, reply_count）。

这些字段是缓存值，通过增量更新维护，在批量导入数据后会不同步。
本脚本通过子查询从关联表重新计算正确值并更新。

用法:
    uv run python scripts/sync_counts.py            # 执行同步
    uv run python scripts/sync_counts.py --dry-run  # 仅查看差异，不写入
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text
from app.database import SessionLocal

SYNC_QUERIES = [
    (
        "boards.post_count",
        """
        SELECT boards.id AS id, boards.name AS name,
               boards.post_count AS current,
               COALESCE(sub.cnt, 0) AS expected
        FROM boards
        LEFT JOIN (
            SELECT board_id, COUNT(*) AS cnt
            FROM posts
            WHERE deleted_at IS NULL AND status = 'normal'
            GROUP BY board_id
        ) sub ON sub.board_id = boards.id
        WHERE boards.deleted_at IS NULL
          AND boards.post_count != COALESCE(sub.cnt, 0)
        ORDER BY boards.name
        """,
        """
        UPDATE boards SET post_count = (
            SELECT COUNT(*) FROM posts
            WHERE posts.board_id = boards.id
              AND posts.deleted_at IS NULL
              AND posts.status = 'normal'
        )
        WHERE deleted_at IS NULL
        """,
    ),
    (
        "posts.comment_count",
        """
        SELECT posts.id AS id, LEFT(posts.title, 40) AS title,
               posts.comment_count AS current,
               COALESCE(sub.cnt, 0) AS expected
        FROM posts
        LEFT JOIN (
            SELECT post_id, COUNT(*) AS cnt
            FROM comments
            WHERE deleted_at IS NULL
            GROUP BY post_id
        ) sub ON sub.post_id = posts.id
        WHERE posts.deleted_at IS NULL
          AND posts.comment_count != COALESCE(sub.cnt, 0)
        ORDER BY posts.created_at DESC
        LIMIT 20
        """,
        """
        UPDATE posts SET comment_count = (
            SELECT COUNT(*) FROM comments
            WHERE comments.post_id = posts.id
              AND comments.deleted_at IS NULL
        )
        WHERE deleted_at IS NULL
        """,
    ),
    (
        "posts.like_count",
        """
        SELECT posts.id AS id, LEFT(posts.title, 40) AS title,
               posts.like_count AS current,
               COALESCE(sub.cnt, 0) AS expected
        FROM posts
        LEFT JOIN (
            SELECT post_id, COUNT(*) AS cnt
            FROM post_likes
            GROUP BY post_id
        ) sub ON sub.post_id = posts.id
        WHERE posts.deleted_at IS NULL
          AND posts.like_count != COALESCE(sub.cnt, 0)
        ORDER BY posts.created_at DESC
        LIMIT 20
        """,
        """
        UPDATE posts SET like_count = (
            SELECT COUNT(*) FROM post_likes
            WHERE post_likes.post_id = posts.id
        )
        WHERE deleted_at IS NULL
        """,
    ),
    (
        "comments.like_count",
        """
        SELECT comments.id AS id, LEFT(comments.content, 40) AS content_preview,
               comments.like_count AS current,
               COALESCE(sub.cnt, 0) AS expected
        FROM comments
        LEFT JOIN (
            SELECT comment_id, COUNT(*) AS cnt
            FROM comment_likes
            GROUP BY comment_id
        ) sub ON sub.comment_id = comments.id
        WHERE comments.deleted_at IS NULL
          AND comments.like_count != COALESCE(sub.cnt, 0)
        LIMIT 20
        """,
        """
        UPDATE comments SET like_count = (
            SELECT COUNT(*) FROM comment_likes
            WHERE comment_likes.comment_id = comments.id
        )
        WHERE deleted_at IS NULL
        """,
    ),
    (
        "comments.reply_count",
        """
        SELECT comments.id AS id, LEFT(comments.content, 40) AS content_preview,
               comments.reply_count AS current,
               COALESCE(sub.cnt, 0) AS expected
        FROM comments
        LEFT JOIN (
            SELECT parent_comment_id, COUNT(*) AS cnt
            FROM comments
            WHERE deleted_at IS NULL AND parent_comment_id IS NOT NULL
            GROUP BY parent_comment_id
        ) sub ON sub.parent_comment_id = comments.id
        WHERE comments.deleted_at IS NULL
          AND comments.reply_count != COALESCE(sub.cnt, 0)
        LIMIT 20
        """,
        """
        UPDATE comments SET reply_count = (
            SELECT COUNT(*) FROM comments c2
            WHERE c2.parent_comment_id = comments.id
              AND c2.deleted_at IS NULL
        )
        WHERE deleted_at IS NULL
        """,
    ),
]


def check_counts(db, dry_run: bool):
    total_mismatches = 0
    total_fixed = 0

    for label, check_sql, update_sql in SYNC_QUERIES:
        result = db.execute(text(check_sql))
        rows = result.fetchall()
        mismatches = len(rows)
        total_mismatches += mismatches

        if mismatches > 0:
            print(f"\n  {label}: {mismatches} 条记录不一致")
            for row in rows:
                id_val = str(row[0])[:8] + "..."
                name_or_title = row[1] if row[1] else "(无标题)"
                current = row[2]
                expected = row[3]
                print(f"    {id_val} {name_or_title}: {current} -> {expected}")
            if not dry_run:
                db.execute(text(update_sql))
                print(f"  ✓ {label} 已同步")
                total_fixed += mismatches
            else:
                print("  (dry-run, 未写入)")
        else:
            print(f"  {label}: ✓ 一致")

    return total_mismatches, total_fixed


def main():
    parser = argparse.ArgumentParser(description="同步数据库中的聚合计数字段")
    parser.add_argument(
        "--dry-run", action="store_true", help="仅查看差异，不写入数据库"
    )
    args = parser.parse_args()

    print("=" * 50)
    print("聚合计数同步工具")
    print("=" * 50)
    if args.dry_run:
        print("模式: dry-run (仅查看)")
    else:
        print("模式: 写入同步")
    print()

    with SessionLocal() as db:
        try:
            print("检查各表计数字段一致性...\n")
            total_mismatches, total_fixed = check_counts(db, args.dry_run)

            print()
            print("=" * 50)
            if total_mismatches == 0:
                print("所有计数字段一致，无需同步。")
            elif args.dry_run:
                print(f"发现 {total_mismatches} 条不一致记录。")
                print("去掉 --dry-run 参数以执行同步。")
            else:
                db.commit()
                print(f"已同步 {total_fixed} 条记录。")
            print("=" * 50)
        except Exception as e:
            db.rollback()
            print(f"\n同步失败: {e}")
            raise


if __name__ == "__main__":
    main()
