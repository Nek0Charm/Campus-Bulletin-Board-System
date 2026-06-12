"""通知任务 — 查看/标记通知。"""

import random

from api_paths import (
    NOTIFICATIONS_LIST,
    NOTIFICATIONS_READ,
    NOTIFICATIONS_READ_ALL,
    NOTIFICATIONS_UNREAD,
)


def view_notifications(self):
    """GET /api/v1/notifications/ — 查看通知列表"""
    if not self.headers:
        return
    page = random.randint(1, 3)
    url = f"{NOTIFICATIONS_LIST}?page={page}&page_size=20"
    with self.client.get(url, headers=self.headers, catch_response=True) as response:
        if response.status_code == 200:
            body = response.json()
            data = body.get("data", {})
            items = data.get("items", [])
            # 缓存通知 ID
            if items:
                self.notification_ids = [item["id"] for item in items]
            response.success()
        else:
            response.failure(f"查看通知失败: HTTP {response.status_code}")


def view_unread_count(self):
    """GET /api/v1/notifications/unread-count — 查看未读通知数"""
    if not self.headers:
        return
    with self.client.get(
        NOTIFICATIONS_UNREAD, headers=self.headers, catch_response=True
    ) as response:
        if response.status_code == 200:
            response.success()
        else:
            response.failure(f"查看未读数失败: HTTP {response.status_code}")


def mark_notification_read(self):
    """PUT /api/v1/notifications/{id}/read — 标记单条通知为已读"""
    if not self.headers:
        return
    notification_ids = getattr(self, "notification_ids", [])
    if not notification_ids:
        return
    notification_id = random.choice(notification_ids)
    url = NOTIFICATIONS_READ.replace("{id}", notification_id)
    with self.client.put(url, headers=self.headers, catch_response=True) as response:
        if response.status_code == 200:
            response.success()
        else:
            response.failure(f"标记通知已读失败: HTTP {response.status_code}")


def mark_all_read(self):
    """PUT /api/v1/notifications/read-all — 标记所有通知为已读"""
    if not self.headers:
        return
    with self.client.put(
        NOTIFICATIONS_READ_ALL, headers=self.headers, catch_response=True
    ) as response:
        if response.status_code == 200:
            response.success()
        else:
            response.failure(f"标记全部已读失败: HTTP {response.status_code}")
