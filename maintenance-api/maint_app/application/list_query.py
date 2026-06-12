from __future__ import annotations

from dataclasses import dataclass

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 200


@dataclass(frozen=True)
class ListQuery:
    page: int = 1
    page_size: int = DEFAULT_PAGE_SIZE
    sort_by: str | None = None
    sort_dir: str = "asc"


def normalize_list_query(
    *,
    page: int | None = None,
    page_size: int | None = None,
    sort_by: str | None = None,
    sort_dir: str | None = None,
) -> ListQuery:
    normalized_page = max(1, int(page or 1))
    normalized_size = max(1, min(int(page_size or DEFAULT_PAGE_SIZE), MAX_PAGE_SIZE))
    direction = "desc" if str(sort_dir or "asc").lower() == "desc" else "asc"
    return ListQuery(
        page=normalized_page,
        page_size=normalized_size,
        sort_by=(sort_by or "").strip() or None,
        sort_dir=direction,
    )


def resolve_sort_column(sort_by: str | None, allowed: dict[str, str], default: str) -> str:
    if sort_by and sort_by in allowed:
        return allowed[sort_by]
    return allowed[default]


def build_order_clause(sort_by: str | None, sort_dir: str, allowed: dict[str, str], default: str) -> str:
    column = resolve_sort_column(sort_by, allowed, default)
    direction = "DESC" if sort_dir == "desc" else "ASC"
    return f"{column} {direction}"


def paginate_slice(items: list, query: ListQuery) -> tuple[list, int]:
    total = len(items)
    if total == 0:
        return [], 0
    start = (query.page - 1) * query.page_size
    end = start + query.page_size
    return items[start:end], total
