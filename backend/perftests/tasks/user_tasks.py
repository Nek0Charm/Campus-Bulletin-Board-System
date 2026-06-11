"""用户任务 — 查看/更新个人资料和统计数据。"""

import random

from api_paths import USERS_ME, USERS_ME_STATS, USERS_PUBLIC


def view_my_profile(self):
    """GET /api/v1/users/me — 查看自己的资料"""
    if not self.headers:
        return
    with self.client.get(
        USERS_ME, headers=self.headers, catch_response=True
    ) as response:
        if response.status_code == 200:
            response.success()
        else:
            response.failure(f"查看个人资料失败: HTTP {response.status_code}")


def view_my_stats(self):
    """GET /api/v1/users/me/stats — 查看自己的统计信息"""
    if not self.headers:
        return
    with self.client.get(
        USERS_ME_STATS, headers=self.headers, catch_response=True
    ) as response:
        if response.status_code == 200:
            response.success()
        else:
            response.failure(f"查看统计信息失败: HTTP {response.status_code}")


def view_public_profile(self):
    """GET /api/v1/users/{id} — 查看其他用户的公开资料"""
    # 使用 post_ids 中的 author_id 或随机从 user pool 中取
    user_ids = getattr(self, "user_ids", [])
    if not user_ids:
        return
    user_id = random.choice(user_ids)
    url = USERS_PUBLIC.replace("{id}", user_id)
    headers = getattr(self, "headers", None)
    with self.client.get(url, headers=headers, catch_response=True) as response:
        if response.status_code == 200:
            response.success()
        else:
            response.failure(f"查看公开资料失败: HTTP {response.status_code}")
