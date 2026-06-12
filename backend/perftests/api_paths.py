"""API 路径常量 — 所有 Locust 任务共用，便于统一维护。"""

# ── 健康检查 ──────────────────────────────────────────────
HEALTH = "/health"

# ── 认证 (Auth) ───────────────────────────────────────────
AUTH_REGISTER = "/api/v1/auth/register"
AUTH_LOGIN = "/api/v1/auth/login"
AUTH_LOGOUT = "/api/v1/auth/logout"
AUTH_VERIFY_EMAIL = "/api/v1/auth/verify-email"
AUTH_RESEND_VERIFY = "/api/v1/auth/resend-verification"
AUTH_RESET_PASSWORD = "/api/v1/auth/reset-password"

# ── 用户 (Users) ──────────────────────────────────────────
USERS_ME = "/api/v1/users/me"
USERS_ME_STATS = "/api/v1/users/me/stats"
USERS_ME_AVATAR = "/api/v1/users/me/avatar"
USERS_PUBLIC = "/api/v1/users/{id}"
USERS_LIST_ADMIN = "/api/v1/users/"
ADMIN_USER_STATUS = "/api/v1/admin/users/{id}/status"

# ── 板块 (Boards) ─────────────────────────────────────────
BOARDS_LIST = "/api/v1/boards/"
BOARDS_DETAIL = "/api/v1/boards/{id}"
BOARDS_MASTERS = "/api/v1/boards/{id}/masters"
BOARDS_MUTE_USER = "/api/v1/boards/{board_id}/users/{user_id}/mute"

# ── 帖子 (Posts) ──────────────────────────────────────────
POSTS_LIST = "/api/v1/posts/"
POSTS_CREATE = "/api/v1/posts/"
POSTS_DETAIL = "/api/v1/posts/{id}"
POSTS_PIN = "/api/v1/posts/{id}/pin"
POSTS_FEATURE = "/api/v1/posts/{id}/feature"

# ── 评论 (Comments) ───────────────────────────────────────
COMMENTS_LIST = "/api/v1/comments/"
COMMENTS_CREATE = "/api/v1/comments/"
COMMENTS_DETAIL = "/api/v1/comments/{comment_id}"

# ── 点赞 (Likes) ──────────────────────────────────────────
LIKES_MY_STATUS = "/api/v1/likes/my-status"
LIKES_POST = "/api/v1/likes/posts/{id}"
LIKES_COMMENT = "/api/v1/likes/comments/{id}"

# ── 通知 (Notifications) ──────────────────────────────────
NOTIFICATIONS_LIST = "/api/v1/notifications/"
NOTIFICATIONS_UNREAD = "/api/v1/notifications/unread-count"
NOTIFICATIONS_READ = "/api/v1/notifications/{id}/read"
NOTIFICATIONS_READ_ALL = "/api/v1/notifications/read-all"

# ── 搜索 (Search) ─────────────────────────────────────────
SEARCH_POSTS = "/api/v1/search/posts"

# ── 公告 (Announcements) ──────────────────────────────────
ANNOUNCEMENTS_LIST = "/api/v1/announcements/"

# ── 媒体 (Media) ──────────────────────────────────────────
MEDIA_UPLOAD = "/api/v1/media/upload"
MEDIA_DETAIL = "/api/v1/media/{id}"
MEDIA_INFO = "/api/v1/media/{id}/info"

# ── 管理后台 (Admin) ───────────────────────────────────────
ADMIN_STATS = "/api/v1/admin/stats"
ADMIN_USERS = "/api/v1/admin/users"
ADMIN_USER_VERIFY = "/api/v1/admin/users/{id}/verify-email"
ADMIN_USER_MUTE = "/api/v1/admin/users/{id}/mute"
ADMIN_BOARDS = "/api/v1/admin/boards"
ADMIN_ANNOUNCEMENTS = "/api/v1/admin/announcements"
