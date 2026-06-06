from datetime import date, datetime, time, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import desc, func, literal_column, or_
from sqlalchemy.orm import Session, joinedload

from app.models.post import Post, PostStatus
from app.schemas.search import SearchSort
from app.utils.search import tokenize_for_search


class SearchService:
    def search_posts(
        self,
        db: Session,
        *,
        keyword: str,
        board_id: Optional[UUID] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        sort_by: SearchSort = SearchSort.RELEVANCE,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Post], int]:
        tokens = tokenize_for_search(keyword)
        if not tokens:
            return [], 0

        if db.bind and db.bind.dialect.name == "postgresql":
            return self._search_postgresql(
                db,
                query_text=" ".join(tokens),
                board_id=board_id,
                start_date=start_date,
                end_date=end_date,
                sort_by=sort_by,
                page=page,
                page_size=page_size,
            )

        return self._search_fallback(
            db,
            tokens=tokens,
            board_id=board_id,
            start_date=start_date,
            end_date=end_date,
            sort_by=sort_by,
            page=page,
            page_size=page_size,
        )

    def _base_query(
        self,
        db: Session,
        *,
        board_id: Optional[UUID],
        start_date: Optional[date],
        end_date: Optional[date],
    ):
        query = (
            db.query(Post)
            .options(joinedload(Post.author))
            .filter(
                Post.deleted_at.is_(None),
                Post.status == PostStatus.NORMAL.value,
            )
        )

        if board_id:
            query = query.filter(Post.board_id == board_id)
        if start_date:
            start_at = datetime.combine(start_date, time.min, tzinfo=timezone.utc)
            query = query.filter(Post.published_at >= start_at)
        if end_date:
            end_at = datetime.combine(end_date, time.max, tzinfo=timezone.utc)
            query = query.filter(Post.published_at <= end_at)
        return query

    def _apply_sorting(self, query, *, sort_by: SearchSort, rank=None):
        hot_score = (Post.like_count * 2) + (Post.comment_count * 3)
        if sort_by == SearchSort.HOT:
            return query.order_by(desc(hot_score), desc(Post.published_at))
        if sort_by == SearchSort.TIME:
            return query.order_by(desc(Post.published_at), desc(Post.created_at))
        if rank is not None:
            return query.order_by(desc(rank), desc(hot_score), desc(Post.published_at))
        return query.order_by(desc(Post.published_at), desc(Post.created_at))

    def _search_postgresql(
        self,
        db: Session,
        *,
        query_text: str,
        board_id: Optional[UUID],
        start_date: Optional[date],
        end_date: Optional[date],
        sort_by: SearchSort,
        page: int,
        page_size: int,
    ) -> tuple[list[Post], int]:
        tsquery = func.websearch_to_tsquery(literal_column("'simple'"), query_text)
        search_vector = literal_column("posts.search_vector")
        rank = func.ts_rank_cd(search_vector, tsquery)

        query = self._base_query(
            db, board_id=board_id, start_date=start_date, end_date=end_date
        ).filter(search_vector.op("@@")(tsquery))
        total = query.count()
        items = (
            self._apply_sorting(query, sort_by=sort_by, rank=rank)
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return items, total

    def _search_fallback(
        self,
        db: Session,
        *,
        tokens: list[str],
        board_id: Optional[UUID],
        start_date: Optional[date],
        end_date: Optional[date],
        sort_by: SearchSort,
        page: int,
        page_size: int,
    ) -> tuple[list[Post], int]:
        query = self._base_query(
            db, board_id=board_id, start_date=start_date, end_date=end_date
        )
        for token in tokens:
            pattern = f"%{token}%"
            query = query.filter(
                or_(
                    Post.title.ilike(pattern),
                    Post.content.ilike(pattern),
                    Post.search_document.ilike(pattern),
                )
            )

        total = query.count()
        items = (
            self._apply_sorting(query, sort_by=sort_by)
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return items, total
