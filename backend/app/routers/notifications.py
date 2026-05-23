from fastapi import APIRouter

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/")
def list_notifications():
    pass


@router.get("/unread-count")
def get_unread_count():
    pass


@router.put("/{notification_id}/read")
def mark_as_read(notification_id: str):
    pass


@router.put("/read-all")
def mark_all_as_read():
    pass
