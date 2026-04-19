from fastapi import APIRouter

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users")
async def admin_list_users():
    pass


@router.put("/users/{user_id}/ban")
async def admin_ban_user(user_id: str):
    pass


@router.put("/users/{user_id}/unban")
async def admin_unban_user(user_id: str):
    pass


@router.put("/boards/{board_id}")
async def admin_update_board(board_id: str):
    pass


@router.delete("/boards/{board_id}")
async def admin_delete_board(board_id: str):
    pass


@router.put("/posts/{post_id}/pin")
async def admin_pin_post(post_id: str):
    pass


@router.put("/posts/{post_id}/feature")
async def admin_feature_post(post_id: str):
    pass


@router.put("/posts/{post_id}/hide")
async def admin_hide_post(post_id: str):
    pass
