"""搜索任务 — 搜索帖子（含板块筛选）。"""

import random

from api_paths import SEARCH_POSTS
from config import DEFAULT_PAGE_SIZE, SEARCH_KEYWORDS


def search_posts(self):
    """GET /api/v1/search/posts — 关键词搜索"""
    keyword = random.choice(SEARCH_KEYWORDS)
    page = random.randint(1, 3)
    url = f"{SEARCH_POSTS}?q={keyword}&page={page}&page_size={DEFAULT_PAGE_SIZE}"
    headers = getattr(self, "headers", None)
    with self.client.get(url, headers=headers, catch_response=True) as response:
        if response.status_code == 200:
            body = response.json()
            if body.get("code") == 200:
                response.success()
            else:
                response.failure(f"搜索业务错误: code={body.get('code')}")
        else:
            response.failure(f"搜索失败: HTTP {response.status_code}")


def search_with_board(self):
    """GET /api/v1/search/posts?q=X&board_id=Y — 搜索并限定板块"""
    if not hasattr(self, "board_ids") or not self.board_ids:
        return
    keyword = random.choice(SEARCH_KEYWORDS)
    board_id = random.choice(self.board_ids)
    url = (
        f"{SEARCH_POSTS}?q={keyword}&board_id={board_id}&page_size={DEFAULT_PAGE_SIZE}"
    )
    headers = getattr(self, "headers", None)
    with self.client.get(
        url, headers=headers, catch_response=True, name=f"{SEARCH_POSTS} [with_board]"
    ) as response:
        if response.status_code == 200:
            response.success()
        else:
            response.failure(f"板块搜索失败: HTTP {response.status_code}")
