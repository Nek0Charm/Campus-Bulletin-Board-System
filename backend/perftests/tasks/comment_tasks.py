"""评论任务 — 创建/回复/查看评论。"""

import random

from api_paths import COMMENTS_CREATE, COMMENTS_LIST
from config import COMMENT_CONTENT_TEMPLATE, DEFAULT_PAGE_SIZE, REPLY_CONTENT_TEMPLATE


def view_comments(self):
    """GET /api/v1/comments/?post_id=X — 查看帖子评论列表"""
    if not self.post_ids:
        return
    post_id = random.choice(self.post_ids)
    headers = getattr(self, "headers", None)
    url = f"{COMMENTS_LIST}?post_id={post_id}&page=1&page_size={DEFAULT_PAGE_SIZE}"
    with self.client.get(url, headers=headers, catch_response=True) as response:
        if response.status_code == 200:
            body = response.json()
            data = body.get("data", {})
            items = data.get("items", [])
            comment_ids = []
            for item in items:
                comment_ids.append(item["id"])
                for reply in item.get("replies", []):
                    comment_ids.append(reply["id"])
            if comment_ids:
                self.comment_ids = comment_ids
            if not hasattr(self, "comment_post_map"):
                self.comment_post_map = {}
            for cid in comment_ids:
                self.comment_post_map[str(cid)] = str(post_id)
            response.success()
        else:
            response.failure(f"查看评论失败: HTTP {response.status_code}")


def create_comment(self):
    """POST /api/v1/comments/ — 创建一级评论"""
    if not self.headers or not self.post_ids:
        return
    post_id = random.choice(self.post_ids)
    n = random.randint(1, 10000)
    payload = {
        "post_id": post_id,
        "content": COMMENT_CONTENT_TEMPLATE.format(n=n),
    }
    with self.client.post(
        COMMENTS_CREATE, json=payload, headers=self.headers, catch_response=True
    ) as response:
        if response.status_code in (200, 201):
            body = response.json()
            data = body.get("data", {})
            comment_id = data.get("id")
            if comment_id:
                cid = str(comment_id)
                self.my_comments.append(cid)
                if hasattr(self, "comment_ids"):
                    self.comment_ids.append(cid)
                if not hasattr(self, "comment_post_map"):
                    self.comment_post_map = {}
                self.comment_post_map[cid] = str(post_id)
            response.success()
        else:
            response.failure(f"创建评论失败: HTTP {response.status_code}")


def create_reply(self):
    """POST /api/v1/comments/ — 创建回复（楼中楼）"""
    if not self.headers:
        return
    comment_ids = getattr(self, "comment_ids", [])
    if not comment_ids:
        return

    parent_comment_id = random.choice(comment_ids)
    comment_post_map = getattr(self, "comment_post_map", {})
    post_id = comment_post_map.get(str(parent_comment_id))
    if not post_id:
        if not self.post_ids:
            return
        post_id = random.choice(self.post_ids)
    n = random.randint(1, 10000)
    payload = {
        "post_id": post_id,
        "content": REPLY_CONTENT_TEMPLATE.format(n=n),
        "parent_comment_id": parent_comment_id,
    }
    with self.client.post(
        COMMENTS_CREATE, json=payload, headers=self.headers, catch_response=True
    ) as response:
        if response.status_code in (200, 201):
            response.success()
        else:
            response.failure(f"创建回复失败: HTTP {response.status_code}")
