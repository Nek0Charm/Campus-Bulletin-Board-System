"""管理员任务 — 系统统计、用户管理、板块管理。"""

import random

from api_paths import (
    ADMIN_ANNOUNCEMENTS,
    ADMIN_BOARDS,
    ADMIN_STATS,
    ADMIN_USERS,
    POSTS_LIST,
)


def admin_view_stats(self):
    """GET /api/v1/admin/stats — 查看系统统计"""
    if not self.headers:
        return
    with self.client.get(
        ADMIN_STATS, headers=self.headers, catch_response=True
    ) as response:
        if response.status_code == 200:
            response.success()
        else:
            response.failure(f"查看系统统计失败: HTTP {response.status_code}")


def admin_list_users(self):
    """GET /api/v1/admin/users — 查看用户列表"""
    if not self.headers:
        return
    page = random.randint(1, 5)
    url = f"{ADMIN_USERS}?page={page}&page_size=20"
    with self.client.get(url, headers=self.headers, catch_response=True) as response:
        if response.status_code == 200:
            body = response.json()
            data = body.get("data", {})
            items = data.get("items", [])
            # 缓存用户 ID 用于后续操作
            if items:
                self.admin_user_ids = [item["id"] for item in items]
            response.success()
        else:
            response.failure(f"查看用户列表失败: HTTP {response.status_code}")


def admin_list_boards(self):
    """GET /api/v1/admin/boards — 查看板块列表"""
    if not self.headers:
        return
    with self.client.get(
        ADMIN_BOARDS, headers=self.headers, catch_response=True
    ) as response:
        if response.status_code == 200:
            response.success()
        else:
            response.failure(f"查看板块列表失败: HTTP {response.status_code}")


def admin_list_announcements(self):
    """GET /api/v1/admin/announcements — 查看公告列表"""
    if not self.headers:
        return
    with self.client.get(
        ADMIN_ANNOUNCEMENTS, headers=self.headers, catch_response=True
    ) as response:
        if response.status_code == 200:
            response.success()
        else:
            response.failure(f"查看公告列表失败: HTTP {response.status_code}")


def admin_browse_posts(self):
    """GET /api/v1/posts/ — 管理员浏览帖子（低频）"""
    if not self.headers:
        return
    page = random.randint(1, 3)
    url = f"{POSTS_LIST}?page={page}&page_size=20"
    with self.client.get(
        url, headers=self.headers, catch_response=True, name=f"{POSTS_LIST} [admin]"
    ) as response:
        if response.status_code == 200:
            response.success()
        else:
            response.failure(f"管理员浏览帖子失败: HTTP {response.status_code}")
