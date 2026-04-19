from fastapi import APIRouter

router = APIRouter(prefix="/posts", tags=["posts"])


@router.get("/")
async def list_posts():
    pass


@router.post("/")
async def create_post():
    pass


@router.get("/{post_id}")
async def get_post(post_id: str):
    pass


@router.put("/{post_id}")
async def update_post(post_id: str):
    pass


@router.delete("/{post_id}")
async def delete_post(post_id: str):
    pass
