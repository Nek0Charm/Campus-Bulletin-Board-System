from pydantic import BaseModel


class AdminStatsResponse(BaseModel):
    total_users: int
    total_posts: int
    total_comments: int
    new_posts_today: int
