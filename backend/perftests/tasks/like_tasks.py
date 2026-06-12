"""点赞任务 — 对帖子/评论点赞、取消点赞、查看状态。"""

import random

from api_paths import LIKES_COMMENT, LIKES_MY_STATUS, LIKES_POST


def like_post(self):
    """POST /api/v1/likes/posts/{id} — 点赞帖子"""
    if not self.headers or not self.post_ids:
        return
    post_id = random.choice(self.post_ids)
    url = LIKES_POST.replace("{id}", post_id)
    with self.client.post(url, headers=self.headers, catch_response=True) as response:
        if response.status_code == 200:
            response.success()
        else:
            # 重复点赞返回 409，视为预期
            if response.status_code == 409:
                response.success()
            else:
                response.failure(f"点赞帖子失败: HTTP {response.status_code}")


def unlike_post(self):
    """DELETE /api/v1/likes/posts/{id} — 取消点赞帖子"""
    if not self.headers or not self.post_ids:
        return
    post_id = random.choice(self.post_ids)
    url = LIKES_POST.replace("{id}", post_id)
    with self.client.delete(url, headers=self.headers, catch_response=True) as response:
        if response.status_code == 200:
            response.success()
        elif response.status_code == 404:
            response.success()
        else:
            response.failure(f"取消点赞帖子失败: HTTP {response.status_code}")


def like_comment(self):
    """POST /api/v1/likes/comments/{id} — 点赞评论"""
    if not self.headers:
        return
    comment_ids = getattr(self, "comment_ids", [])
    if not comment_ids:
        return
    comment_id = random.choice(comment_ids)
    url = LIKES_COMMENT.replace("{id}", comment_id)
    with self.client.post(url, headers=self.headers, catch_response=True) as response:
        if response.status_code == 200:
            response.success()
        elif response.status_code == 409:
            response.success()
        else:
            response.failure(f"点赞评论失败: HTTP {response.status_code}")


def unlike_comment(self):
    """DELETE /api/v1/likes/comments/{id} — 取消点赞评论"""
    if not self.headers:
        return
    comment_ids = getattr(self, "comment_ids", [])
    if not comment_ids:
        return
    comment_id = random.choice(comment_ids)
    url = LIKES_COMMENT.replace("{id}", comment_id)
    with self.client.delete(url, headers=self.headers, catch_response=True) as response:
        if response.status_code == 200:
            response.success()
        elif response.status_code == 404:
            response.success()
        else:
            response.failure(f"取消点赞评论失败: HTTP {response.status_code}")


def check_like_status(self):
    """GET /api/v1/likes/my-status?post_id=X — 查看自己的点赞状态"""
    if not self.headers or not self.post_ids:
        return
    post_id = random.choice(self.post_ids)
    url = f"{LIKES_MY_STATUS}?post_id={post_id}"
    with self.client.get(url, headers=self.headers, catch_response=True) as response:
        if response.status_code == 200:
            response.success()
        else:
            response.failure(f"查看点赞状态失败: HTTP {response.status_code}")
