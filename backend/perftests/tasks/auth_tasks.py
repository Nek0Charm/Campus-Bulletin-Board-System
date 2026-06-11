"""认证任务 — 登录/登出。"""

from api_paths import AUTH_LOGOUT


def logout_task(self):
    """POST /api/v1/auth/logout — 登出（会使当前 Token 失效）"""
    if not self.headers:
        return
    with self.client.post(
        AUTH_LOGOUT, headers=self.headers, catch_response=True
    ) as response:
        if response.status_code == 200:
            response.success()
            # 登出后清除 Token，下次任务需要重新登录
            self.token = None
            self.headers = None
        else:
            response.failure(f"登出失败: HTTP {response.status_code}")
