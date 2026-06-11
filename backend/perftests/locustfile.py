"""
校园论坛性能测试 — 主 Locust 测试脚本。

包含四种用户类型，模拟真实校园论坛使用场景：
  - AnonymousBrowserUser (权重 3): 匿名浏览用户
  - AuthenticatedBrowserUser (权重 5): 已认证浏览+互动用户
  - ActivePosterUser (权重 2): 活跃发帖用户
  - AdminUser (权重 1): 管理员

运行方式:
    cd backend && uv run locust -f perftests/locustfile.py          # Web UI 模式
    cd backend && uv run locust -f perftests/locustfile.py --headless -u 50 -r 10 -t 5m
"""

import sys
from pathlib import Path

# 将 backend 目录加入 sys.path，使 perftests 内部模块可以互相导入
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from locust import HttpUser, between, task

from auth_helpers import (
    fetch_board_ids,
    fetch_post_ids,
    login,
    load_user_pool,
    pick_random_admin_user,
    pick_random_regular_user,
)
from config import DEFAULT_HOST
from tasks.admin_tasks import (
    admin_browse_posts,
    admin_list_announcements,
    admin_list_boards,
    admin_list_users,
    admin_view_stats,
)
from tasks.browse_tasks import (
    browse_announcements,
    browse_boards_detail,
    browse_boards_list,
    browse_health,
    browse_posts_detail,
    browse_posts_list,
    browse_search,
)
from tasks.comment_tasks import create_comment, create_reply, view_comments
from tasks.like_tasks import (
    check_like_status,
    like_comment,
    like_post,
    unlike_post,
)
from tasks.notification_tasks import (
    mark_all_read,
    mark_notification_read,
    view_notifications,
    view_unread_count,
)
from tasks.post_tasks import (
    create_post,
    edit_own_post,
    view_post_detail_authed,
    view_posts_list_authed,
)
from tasks.search_tasks import search_posts
from tasks.user_tasks import view_my_profile, view_my_stats


class AnonymousBrowserUser(HttpUser):
    """匿名浏览用户 — 不登录，只查看公共内容。"""

    weight = 3
    wait_time = between(2, 8)
    host = DEFAULT_HOST

    def on_start(self):
        """初始化时缓存板块和帖子 ID。"""
        self.board_ids = fetch_board_ids(self.client)
        self.post_ids = fetch_post_ids(self.client)

    @task(2)
    def t_health(self):
        browse_health(self)

    @task(5)
    def t_boards_list(self):
        browse_boards_list(self)

    @task(3)
    def t_boards_detail(self):
        browse_boards_detail(self)

    @task(10)
    def t_posts_list(self):
        browse_posts_list(self)

    @task(8)
    def t_posts_detail(self):
        browse_posts_detail(self)

    @task(4)
    def t_search(self):
        browse_search(self)

    @task(2)
    def t_announcements(self):
        browse_announcements(self)


class AuthenticatedBrowserUser(HttpUser):
    """已认证浏览用户 — 登录后浏览、点赞、评论、查看通知。"""

    weight = 5
    wait_time = between(1, 5)
    host = DEFAULT_HOST

    def on_start(self):
        """登录并缓存数据 ID。"""
        pool = load_user_pool()
        username, password = pick_random_regular_user(pool)
        self.token = login(self.client, username, password)
        if self.token:
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            self.headers = None
        self.board_ids = fetch_board_ids(self.client, self.headers)
        self.post_ids = fetch_post_ids(self.client, self.headers)
        self.comment_ids = []
        self.notification_ids = []

    @task(10)
    def t_posts_list(self):
        view_posts_list_authed(self)

    @task(8)
    def t_posts_detail(self):
        view_post_detail_authed(self)

    @task(5)
    def t_comments(self):
        view_comments(self)

    @task(3)
    def t_like_post(self):
        like_post(self)

    @task(1)
    def t_unlike_post(self):
        unlike_post(self)

    @task(2)
    def t_like_comment(self):
        like_comment(self)

    @task(2)
    def t_check_like_status(self):
        check_like_status(self)

    @task(3)
    def t_notifications(self):
        view_notifications(self)

    @task(2)
    def t_unread_count(self):
        view_unread_count(self)

    @task(1)
    def t_mark_read(self):
        mark_notification_read(self)

    @task(1)
    def t_mark_all_read(self):
        mark_all_read(self)

    @task(4)
    def t_search(self):
        search_posts(self)

    @task(2)
    def t_my_profile(self):
        view_my_profile(self)

    @task(1)
    def t_my_stats(self):
        view_my_stats(self)


class ActivePosterUser(HttpUser):
    """活跃发帖用户 — 频繁创建帖子、评论和回复。"""

    weight = 2
    wait_time = between(2, 6)
    host = DEFAULT_HOST

    def on_start(self):
        """登录并初始化数据追踪列表。"""
        pool = load_user_pool()
        username, password = pick_random_regular_user(pool)
        self.token = login(self.client, username, password)
        if self.token:
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            self.headers = None
        self.board_ids = fetch_board_ids(self.client, self.headers)
        self.post_ids = fetch_post_ids(self.client, self.headers)
        self.my_posts = []
        self.my_comments = []
        self.comment_ids = []
        self.notification_ids = []

    @task(5)
    def t_create_post(self):
        create_post(self)

    @task(6)
    def t_post_detail(self):
        view_post_detail_authed(self)

    @task(4)
    def t_create_comment(self):
        create_comment(self)

    @task(3)
    def t_create_reply(self):
        create_reply(self)

    @task(3)
    def t_like_post(self):
        like_post(self)

    @task(3)
    def t_view_comments(self):
        view_comments(self)

    @task(2)
    def t_notifications(self):
        view_notifications(self)

    @task(2)
    def t_boards_list(self):
        browse_boards_list(self)

    @task(1)
    def t_edit_own_post(self):
        edit_own_post(self)


class AdminUser(HttpUser):
    """管理员用户 — 系统统计、用户和板块管理。"""

    weight = 1
    wait_time = between(3, 10)
    host = DEFAULT_HOST

    def on_start(self):
        """以管理员身份登录。"""
        pool = load_user_pool()
        username, password = pick_random_admin_user(pool)
        self.token = login(self.client, username, password)
        if self.token:
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            self.headers = None
        self.board_ids = fetch_board_ids(self.client, self.headers)
        self.post_ids = fetch_post_ids(self.client, self.headers)
        self.admin_user_ids = []

    @task(5)
    def t_admin_stats(self):
        admin_view_stats(self)

    @task(4)
    def t_admin_users(self):
        admin_list_users(self)

    @task(2)
    def t_admin_boards(self):
        admin_list_boards(self)

    @task(2)
    def t_admin_announcements(self):
        admin_list_announcements(self)

    @task(3)
    def t_browse_posts(self):
        admin_browse_posts(self)
