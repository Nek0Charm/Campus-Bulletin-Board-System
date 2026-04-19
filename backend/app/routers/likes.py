from fastapi import APIRouter

router = APIRouter(prefix="/likes", tags=["likes"])


@router.post("/post/{post_id}")
async def like_post(post_id: str):
    pass


@router.delete("/post/{post_id}")
async def unlike_post(post_id: str):
    pass


@router.post("/comment/{comment_id}")
async def like_comment(comment_id: str):
    pass


@router.delete("/comment/{comment_id}")
async def unlike_comment(comment_id: str):
    pass
