"""Locust 性能测试配置常量。"""

from pathlib import Path

# 服务地址
DEFAULT_HOST = "http://localhost:8000"
API_PREFIX = "/api/v1"

# 用户等待时间（秒）
WAIT_MIN = 1
WAIT_MAX = 5

# 用户凭据池路径
USER_POOL_PATH = Path(__file__).resolve().parent / "user_pool.json"

# 测试场景参数（可通过 Locust 命令行参数覆盖）
BASELINE_USERS = 50
BASELINE_RUNTIME = "5m"
LOAD_MAX_USERS = 500
STRESS_MAX_USERS = 1000

# 搜索关键词（来自校园论坛常见话题）
SEARCH_KEYWORDS = ["学习", "Python", "推荐", "求职", "二手", "考试", "实习", "食堂"]

# 帖子内容模板
POST_TITLE_TEMPLATE = "性能测试帖子 #{n}"
POST_CONTENT_TEMPLATE = (
    "这是一条由性能测试工具自动生成的帖子内容，编号 #{n}。"
    "主要用于验证系统在高并发下的发帖功能稳定性。"
)

# 评论内容模板
COMMENT_CONTENT_TEMPLATE = "性能测试评论 #{n} — 验证并发评论功能。"
REPLY_CONTENT_TEMPLATE = "回复评论 #{n} — 验证楼中楼回复功能。"

# 默认密码（与 seed_data.py 一致）
PERFTEST_DEFAULT_PASSWORD = "PerfTest123!"

# 分页默认参数
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# 响应码
RESPONSE_CODE_SUCCESS = 200
