"""帖子任务 — 创建/浏览/编辑帖子。"""

import random

from api_paths import POSTS_CREATE, POSTS_DETAIL, POSTS_LIST
from config import DEFAULT_PAGE_SIZE, POST_CONTENT_TEMPLATE, POST_TITLE_TEMPLATE


def create_post(self):
    """POST /api/v1/posts/ — 创建帖子"""
    if not self.headers or not self.board_ids:
        return
    n = random.randint(1, 10000)
    board_id = random.choice(self.board_ids)
    payload = {
        "title": POST_TITLE_TEMPLATE.format(n=n),
        "content": POST_CONTENT_TEMPLATE.format(n=n),
        "board_id": board_id,
    }
    with self.client.post(
        POSTS_CREATE, json=payload, headers=self.headers, catch_response=True
    ) as response:
        if response.status_code == 201:
            body = response.json()
            data = body.get("data", {})
            post_id = data.get("id")
            if post_id:
                self.my_posts.append(str(post_id))
                self.post_ids.append(str(post_id))
            response.success()
        elif response.status_code == 200:
            body = response.json()
            if body.get("code") == 200:
                data = body.get("data", {})
                post_id = data.get("id")
                if post_id:
                    self.my_posts.append(str(post_id))
                    self.post_ids.append(str(post_id))
                response.success()
            else:
                response.failure(f"创建帖子业务错误: code={body.get('code')}")
        else:
            response.failure(f"创建帖子失败: HTTP {response.status_code}")


def view_posts_list_authed(self):
    """GET /api/v1/posts/ — 已认证用户浏览帖子列表（包含 is_liked 信息）"""
    if not self.headers:
        return
    page = random.randint(1, 5)
    board_id = random.choice(self.board_ids) if self.board_ids else ""
    params = f"?page={page}&page_size={DEFAULT_PAGE_SIZE}"
    if board_id:
        params += f"&board_id={board_id}"
    with self.client.get(
        POSTS_LIST + params,
        headers=self.headers,
        catch_response=True,
        name=f"{POSTS_LIST} [authed]",
    ) as response:
        if response.status_code == 200:
            response.success()
        else:
            response.failure(f"浏览帖子列表失败: HTTP {response.status_code}")


def view_post_detail_authed(self):
    """GET /api/v1/posts/{id} — 已认证用户查看帖子详情"""
    if not self.headers or not self.post_ids:
        return
    post_id = random.choice(self.post_ids)
    url = POSTS_DETAIL.replace("{id}", post_id)
    with self.client.get(url, headers=self.headers, catch_response=True) as response:
        if response.status_code == 200:
            response.success()
        else:
            response.failure(f"查看帖子详情失败: HTTP {response.status_code}")


def edit_own_post(self):
    """PATCH /api/v1/posts/{id} — 编辑自己的帖子"""
    if not self.headers or not self.my_posts:
        return
    post_id = random.choice(self.my_posts)
    url = POSTS_DETAIL.replace("{id}", post_id)
    n = random.randint(1, 10000)
    payload = {
        "title": f"编辑后的帖子 #{n}",
        "content": f"这是编辑后的内容 #{n}，验证编辑功能在并发下的稳定性。",
    }
    with self.client.patch(
        url, json=payload, headers=self.headers, catch_response=True
    ) as response:
        if response.status_code == 200:
            response.success()
        else:
            # 编辑他人帖子或已删除帖子会 403/404，视为预期行为
            response.failure(f"编辑帖子失败: HTTP {response.status_code}")
