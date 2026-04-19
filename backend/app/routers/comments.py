from fastapi import APIRouter

router = APIRouter(prefix="/comments", tags=["comments"])


@router.get("/{post_id}")
async def list_comments(post_id: str):
    pass


@router.post("/{post_id}")
async def create_comment(post_id: str):
    pass


@router.delete("/{comment_id}")
async def delete_comment(comment_id: str):
    pass
