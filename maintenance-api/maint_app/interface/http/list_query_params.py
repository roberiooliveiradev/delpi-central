from __future__ import annotations

from typing import Optional

from fastapi import Query

from maint_app.application.list_query import ListQuery, normalize_list_query


def list_query_params(
    page: Optional[int] = Query(1, ge=1),
    page_size: Optional[int] = Query(20, ge=1, le=200),
    sort_by: Optional[str] = Query(None),
    sort_dir: Optional[str] = Query("asc", pattern="^(asc|desc)$"),
) -> ListQuery:
    return normalize_list_query(
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_dir=sort_dir,
    )
