"""匿名浏览任务 — 不需要认证的公共接口。"""

import random

from api_paths import (
    ANNOUNCEMENTS_LIST,
    BOARDS_DETAIL,
    BOARDS_LIST,
    HEALTH,
    POSTS_DETAIL,
    POSTS_LIST,
    SEARCH_POSTS,
)
from config import DEFAULT_PAGE_SIZE, SEARCH_KEYWORDS


def browse_health(self):
    """GET /health — 健康检查"""
    with self.client.get(HEALTH, catch_response=True) as response:
        if response.status_code == 200:
            response.success()
        else:
            response.failure(f"健康检查失败: HTTP {response.status_code}")


def browse_boards_list(self):
    """GET /api/v1/boards/ — 获取板块列表"""
    with self.client.get(BOARDS_LIST, catch_response=True) as response:
        if response.status_code == 200:
            body = response.json()
            if body.get("code") == 200:
                response.success()
            else:
                response.failure(f"业务错误: code={body.get('code')}")
        else:
            response.failure(f"获取板块列表失败: HTTP {response.status_code}")


def browse_boards_detail(self):
    """GET /api/v1/boards/{id} — 获取板块详情"""
    if not self.board_ids:
        return
    board_id = random.choice(self.board_ids)
    url = BOARDS_DETAIL.replace("{id}", board_id)
    with self.client.get(url, catch_response=True) as response:
        if response.status_code == 200:
            response.success()
        else:
            response.failure(f"获取板块详情失败: HTTP {response.status_code}")


def browse_posts_list(self):
    """GET /api/v1/posts/ — 浏览帖子列表"""
    page = random.randint(1, 5)
    board_id = random.choice(self.board_ids) if self.board_ids else ""
    params = f"?page={page}&page_size={DEFAULT_PAGE_SIZE}"
    if board_id:
        params += f"&board_id={board_id}"
    with self.client.get(
        POSTS_LIST + params, catch_response=True, name=f"{POSTS_LIST} [browse]"
    ) as response:
        if response.status_code == 200:
            body = response.json()
            if body.get("code") == 200:
                response.success()
            else:
                response.failure(f"业务错误: code={body.get('code')}")
        else:
            response.failure(f"获取帖子列表失败: HTTP {response.status_code}")


def browse_posts_detail(self):
    """GET /api/v1/posts/{id} — 浏览帖子详情"""
    if not self.post_ids:
        return
    post_id = random.choice(self.post_ids)
    url = POSTS_DETAIL.replace("{id}", post_id)
    with self.client.get(url, catch_response=True) as response:
        if response.status_code == 200:
            response.success()
        else:
            response.failure(f"获取帖子详情失败: HTTP {response.status_code}")


def browse_search(self):
    """GET /api/v1/search/posts — 搜索帖子"""
    keyword = random.choice(SEARCH_KEYWORDS)
    page = random.randint(1, 3)
    url = f"{SEARCH_POSTS}?q={keyword}&page={page}&page_size={DEFAULT_PAGE_SIZE}"
    with self.client.get(url, catch_response=True) as response:
        if response.status_code == 200:
            body = response.json()
            if body.get("code") == 200:
                response.success()
            else:
                response.failure(f"搜索业务错误: code={body.get('code')}")
        else:
            response.failure(f"搜索失败: HTTP {response.status_code}")


def browse_announcements(self):
    """GET /api/v1/announcements/ — 浏览公告"""
    with self.client.get(ANNOUNCEMENTS_LIST, catch_response=True) as response:
        if response.status_code == 200:
            response.success()
        else:
            response.failure(f"获取公告失败: HTTP {response.status_code}")
