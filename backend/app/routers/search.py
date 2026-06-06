from datetime import date
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.deps.db import get_db
from app.deps.services import get_search_service
from app.schemas.post import PostRead
from app.schemas.response import PaginatedData, PaginatedResponse, PaginationInfo
from app.schemas.search import SearchSort
from app.services.search_service import SearchService

router = APIRouter(prefix="/search", tags=["Search"])


@router.get("/posts", response_model=PaginatedResponse[PostRead])
def search_posts(
    q: str = Query(..., min_length=1, max_length=100, description="搜索关键词"),
    board_id: Optional[UUID] = Query(None, description="限定板块 ID"),
    start_date: Optional[date] = Query(None, description="起始发布日期"),
    end_date: Optional[date] = Query(None, description="结束发布日期"),
    sort_by: SearchSort = Query(SearchSort.RELEVANCE, description="排序方式"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    service: SearchService = Depends(get_search_service),
):
    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=400, detail="start_date must be before end_date"
        )

    items, total = service.search_posts(
        db,
        keyword=q,
        board_id=board_id,
        start_date=start_date,
        end_date=end_date,
        sort_by=sort_by,
        page=page,
        page_size=page_size,
    )
    return PaginatedResponse(
        data=PaginatedData(
            items=items,
            pagination=PaginationInfo(
                page=page,
                page_size=page_size,
                total=total,
                total_pages=(total + page_size - 1) // page_size,
            ),
        )
    )
