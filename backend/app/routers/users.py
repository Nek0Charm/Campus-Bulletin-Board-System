from fastapi import APIRouter

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me")
async def get_current_user_profile():
    pass


@router.put("/me")
async def update_current_user_profile():
    pass
