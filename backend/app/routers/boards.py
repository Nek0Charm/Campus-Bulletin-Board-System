from fastapi import APIRouter

router = APIRouter(prefix="/boards", tags=["boards"])


@router.get("/")
async def list_boards():
    pass


@router.post("/")
async def create_board():
    pass


@router.get("/{board_id}")
async def get_board(board_id: str):
    pass
