from __future__ import annotations

from fastapi.params import Query as QueryParam

from app.application.services.pagination_envelope_builder import PaginationEnvelopeBuilder
from app.interface.http.pagination_query import (
    HISTORY_LIMIT_QUERY,
    LIMIT_QUERY,
    PAGE_SIZE_QUERY,
    TOP_LIMIT_QUERY,
)


def _constraint(q: QueryParam, name: str):
    for item in q.metadata or []:
        if hasattr(item, name):
            return getattr(item, name)
    return None


def test_page_size_query_uses_tier_bounds() -> None:
    q = PAGE_SIZE_QUERY("page_50_500")
    assert isinstance(q, QueryParam)
    assert q.default == 50
    assert _constraint(q, "ge") == 1
    assert _constraint(q, "le") == 500


def test_optional_page_size_query() -> None:
    q = PAGE_SIZE_QUERY("page_optional_500")
    assert q.default is None
    assert _constraint(q, "le") == 500


def test_limit_and_top_and_history_factories() -> None:
    assert LIMIT_QUERY("limit_rol_8000").default == 8000
    assert TOP_LIMIT_QUERY("top_limit_5_20").default == 5
    assert HISTORY_LIMIT_QUERY("history_limit_optional_200").default is None


def test_envelope_shapes() -> None:
    paged = PaginationEnvelopeBuilder.paged_count(page=1, page_size=50, total=120)
    assert paged["total_pages"] == 3
    assert paged["is_complete"] is False

    over = PaginationEnvelopeBuilder.overfetch(
        limit=50, offset=0, returned=50, is_complete=False, total=200
    )
    assert over["limit"] == 50 and over["total"] == 200

    nxt = PaginationEnvelopeBuilder.has_next(page=2, page_size=25, has_next=True)
    assert nxt["is_complete"] is False

    tree = PaginationEnvelopeBuilder.full_tree(page_size=None, returned=10)
    assert tree["is_complete"] is True
    assert "page_size" not in tree
