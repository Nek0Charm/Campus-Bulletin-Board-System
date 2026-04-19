from fastapi import APIRouter

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/")
async def list_notifications():
    pass


@router.get("/unread-count")
async def get_unread_count():
    pass


@router.put("/{notification_id}/read")
async def mark_as_read(notification_id: str):
    pass


@router.put("/read-all")
async def mark_all_as_read():
    pass
