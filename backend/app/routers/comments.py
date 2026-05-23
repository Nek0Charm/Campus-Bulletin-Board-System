from fastapi import APIRouter

router = APIRouter(prefix="/comments", tags=["comments"])


@router.get("/{post_id}")
def list_comments(post_id: str):
    pass


@router.post("/{post_id}")
def create_comment(post_id: str):
    pass


@router.delete("/{comment_id}")
def delete_comment(comment_id: str):
    pass
