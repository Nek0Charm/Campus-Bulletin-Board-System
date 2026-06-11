"""
校园论坛性能测试 — 接口专项测试脚本。

每种 HttpUser 只执行一种任务，用于独立测量各接口的 P95 响应时间。

性能目标 (P95):
  - 登录: < 300ms
  - 帖子列表: < 200ms
  - 帖子详情: < 150ms
  - 板块列表: < 100ms
  - 创建帖子: < 500ms
  - 搜索: < 500ms

运行方式:
    cd backend && uv run locust -f perftests/locustfile_interfaces.py --headless -u 50 -r 10 -t 3m
    cd backend && uv run locust -f perftests/locustfile_interfaces.py    # Web UI 模式
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from locust import HttpUser, between, task

from auth_helpers import (
    fetch_board_ids,
    fetch_post_ids,
    login,
    load_user_pool,
    pick_random_regular_user,
)
from config import (
    DEFAULT_HOST,
    DEFAULT_PAGE_SIZE,
    POST_CONTENT_TEMPLATE,
    POST_TITLE_TEMPLATE,
    SEARCH_KEYWORDS,
)
from api_paths import (
    AUTH_LOGIN,
    BOARDS_LIST,
    POSTS_CREATE,
    POSTS_DETAIL,
    POSTS_LIST,
    SEARCH_POSTS,
)


class LoginOnlyUser(HttpUser):
    """仅测试登录接口 — P95 目标 < 300ms"""

    weight = 1
    wait_time = between(0.5, 2)
    host = DEFAULT_HOST

    def on_start(self):
        pool = load_user_pool()
        self.pool = pool

    @task
    def t_login(self):
        username, password = pick_random_regular_user(self.pool)
        with self.client.post(
            AUTH_LOGIN,
            json={"account": username, "password": password},
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                body = response.json()
                token = body.get("data", {}).get("access_token")
                if token:
                    response.success()
                else:
                    response.failure("响应中无 access_token")
            else:
                response.failure(f"登录失败: HTTP {response.status_code}")


class PostsListOnlyUser(HttpUser):
    """仅测试帖子列表接口 — P95 目标 < 200ms"""

    weight = 1
    wait_time = between(0.5, 2)
    host = DEFAULT_HOST

    def on_start(self):
        self.board_ids = fetch_board_ids(self.client)

    @task
    def t_posts_list(self):
        page = 1
        url = f"{POSTS_LIST}?page={page}&page_size={DEFAULT_PAGE_SIZE}"
        with self.client.get(
            url, catch_response=True, name=f"{POSTS_LIST} [interface]"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"HTTP {response.status_code}")


class PostDetailOnlyUser(HttpUser):
    """仅测试帖子详情接口 — P95 目标 < 150ms"""

    weight = 1
    wait_time = between(0.5, 2)
    host = DEFAULT_HOST

    def on_start(self):
        self.post_ids = fetch_post_ids(self.client, page_size=50)

    @task
    def t_post_detail(self):
        if not self.post_ids:
            return
        import random

        post_id = random.choice(self.post_ids)
        url = POSTS_DETAIL.replace("{id}", post_id)
        with self.client.get(
            url, catch_response=True, name=f"{POSTS_DETAIL} [interface]"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"HTTP {response.status_code}")


class BoardsListOnlyUser(HttpUser):
    """仅测试板块列表接口 — P95 目标 < 100ms"""

    weight = 1
    wait_time = between(0.5, 2)
    host = DEFAULT_HOST

    @task
    def t_boards_list(self):
        with self.client.get(
            BOARDS_LIST, catch_response=True, name=f"{BOARDS_LIST} [interface]"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"HTTP {response.status_code}")


class CreatePostOnlyUser(HttpUser):
    """仅测试创建帖子接口 — P95 目标 < 500ms"""

    weight = 1
    wait_time = between(0.5, 2)
    host = DEFAULT_HOST

    def on_start(self):
        pool = load_user_pool()
        username, password = pick_random_regular_user(pool)
        self.token = login(self.client, username, password)
        if self.token:
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            self.headers = None
        self.board_ids = fetch_board_ids(self.client, self.headers)

    @task
    def t_create_post(self):
        if not self.headers or not self.board_ids:
            return
        import random

        n = random.randint(1, 100000)
        board_id = random.choice(self.board_ids)
        payload = {
            "title": POST_TITLE_TEMPLATE.format(n=n),
            "content": POST_CONTENT_TEMPLATE.format(n=n),
            "board_id": board_id,
        }
        with self.client.post(
            POSTS_CREATE,
            json=payload,
            headers=self.headers,
            catch_response=True,
            name=f"{POSTS_CREATE} [interface]",
        ) as response:
            if response.status_code in (200, 201):
                response.success()
            else:
                response.failure(f"HTTP {response.status_code}")


class SearchOnlyUser(HttpUser):
    """仅测试搜索接口 — P95 目标 < 500ms"""

    weight = 1
    wait_time = between(0.5, 2)
    host = DEFAULT_HOST

    @task
    def t_search(self):
        import random

        keyword = random.choice(SEARCH_KEYWORDS)
        url = f"{SEARCH_POSTS}?q={keyword}&page=1&page_size={DEFAULT_PAGE_SIZE}"
        with self.client.get(
            url, catch_response=True, name=f"{SEARCH_POSTS} [interface]"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"HTTP {response.status_code}")
