"""Unit tests — paged_list envelope helpers."""

from __future__ import annotations

from app.application.services.paged_list_envelope_service import (
    build_has_next_pagination,
    build_paged_list_envelope,
)


def test_build_paged_list_envelope_with_total() -> None:
    payload = build_paged_list_envelope(
        page=1,
        page_size=25,
        total=40,
        items=[{"id": 1}],
    )
    assert payload["total"] == 40
    assert payload["total_pages"] == 2
    assert payload["pagination"]["is_complete"] is False
    assert payload["pagination"]["total"] == 40


def test_build_has_next_pagination_incomplete() -> None:
    assert build_has_next_pagination(page=1, page_size=25, has_next=True) == {
        "page": 1,
        "page_size": 25,
        "is_complete": False,
    }


def test_build_has_next_pagination_complete() -> None:
    assert build_has_next_pagination(page=2, page_size=10, has_next=False) == {
        "page": 2,
        "page_size": 10,
        "is_complete": True,
    }
