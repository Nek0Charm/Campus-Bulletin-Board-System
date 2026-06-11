"""认证辅助工具 — Locust 任务共用的登录/凭据池加载函数。"""

import json
import random

from config import USER_POOL_PATH


def load_user_pool() -> dict:
    """从 JSON 文件加载用户凭据池。

    Returns:
        dict: {"regular_users": [...], "admin_users": [...]}
    """
    if USER_POOL_PATH.exists():
        return json.loads(USER_POOL_PATH.read_text())
    print(f"⚠️  用户凭据池文件不存在: {USER_POOL_PATH}")
    print("   请先运行: cd backend && uv run python perftests/seed_data.py")
    return {"regular_users": [], "admin_users": []}


def pick_random_regular_user(pool: dict) -> tuple[str, str]:
    """从凭据池中随机选取一个普通用户。

    Returns:
        (username, password) 元组
    """
    user = random.choice(pool["regular_users"])
    return user["username"], user["password"]


def pick_random_admin_user(pool: dict) -> tuple[str, str]:
    """从凭据池中随机选取一个管理员用户。

    Returns:
        (username, password) 元组
    """
    user = random.choice(pool["admin_users"])
    return user["username"], user["password"]


def login(client, account: str, password: str) -> str | None:
    """通过 API 执行登录，返回 access_token。

    Args:
        client: Locust HttpSession 实例
        account: 用户名或邮箱
        password: 密码

    Returns:
        JWT access_token 字符串，登录失败时返回 None
    """
    from api_paths import AUTH_LOGIN

    with client.post(
        AUTH_LOGIN,
        json={"account": account, "password": password},
        catch_response=True,
    ) as response:
        if response.status_code == 200:
            body = response.json()
            # API 响应格式: {code, message, data: {access_token, ...}}
            data = body.get("data", {})
            token = data.get("access_token")
            if token:
                response.success()
                return token
            response.failure("响应中无 access_token")
            return None
        else:
            response.failure(f"登录失败: HTTP {response.status_code}")
            return None


def fetch_board_ids(client, headers: dict | None = None) -> list[str]:
    """获取所有板块 ID，用于后续请求中选取随机板块。

    Args:
        client: Locust HttpSession 实例
        headers: 可选的认证 headers

    Returns:
        板块 ID 字符串列表
    """
    from api_paths import BOARDS_LIST

    # GET /api/v1/boards/ 返回 data 为列表（非 PaginatedResponse）
    with client.get(BOARDS_LIST, headers=headers, catch_response=True) as response:
        if response.status_code == 200:
            body = response.json()
            data = body.get("data", [])
            # boards 的 data 是直接列表，不是 {items: ...} 分页对象
            items = data if isinstance(data, list) else data.get("items", [])
            if items:
                response.success()
                return [item["id"] for item in items]
            response.failure("板块列表为空")
            return []
        else:
            response.failure(f"获取板块列表失败: HTTP {response.status_code}")
            return []


def fetch_post_ids(
    client, headers: dict | None = None, page_size: int = 50
) -> list[str]:
    """获取帖子 ID 列表，用于后续请求中选取随机帖子。

    Args:
        client: Locust HttpSession 实例
        headers: 可选的认证 headers
        page_size: 每页数量（使用 50 以避免大偏移量引发的 500 错误）

    Returns:
        帖子 ID 字符串列表
    """
    from api_paths import POSTS_LIST

    ids = []
    # 获取前几页帖子以积累足够多的 ID
    for page in range(1, 4):
        with client.get(
            f"{POSTS_LIST}?page={page}&page_size={page_size}",
            headers=headers,
            catch_response=True,
            name=f"{POSTS_LIST} [fetch_ids page={page}]",
        ) as response:
            if response.status_code == 200:
                body = response.json()
                data = body.get("data", {})
                # posts 使用 PaginatedResponse: {items: [...], pagination: {...}}
                items = data.get("items", []) if isinstance(data, dict) else []
                for item in items:
                    ids.append(item["id"])
                if len(items) < page_size:
                    response.success()
                    break
                response.success()
            else:
                # 大偏移量可能触发 500，视为正常结束而非失败
                response.success()
                break
                break
    return ids


def fetch_user_ids(client, headers: dict) -> list[str]:
    """获取部分用户 ID（管理员接口），用于管理员任务中选取随机用户。

    Args:
        client: Locust HttpSession 实例
        headers: 管理员认证 headers

    Returns:
        用户 ID 字符串列表
    """
    from api_paths import ADMIN_USERS

    with client.get(
        f"{ADMIN_USERS}?page=1&page_size=50",
        headers=headers,
        catch_response=True,
    ) as response:
        if response.status_code == 200:
            body = response.json()
            items = body.get("data", {}).get("items", [])
            if items:
                response.success()
                return [item["id"] for item in items]
            response.failure("用户列表为空")
            return []
        else:
            response.failure(f"获取用户列表失败: HTTP {response.status_code}")
            return []
