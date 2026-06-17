from app.application.services.production.operational_limit_page_service import (
    build_operational_pagination,
    overfetch_limit,
    trim_overfetched,
)


def test_overfetch_limit_adds_one() -> None:
    assert overfetch_limit(50) == 51


def test_trim_overfetched_complete_when_at_or_below_limit() -> None:
    items, is_complete = trim_overfetched([{"a": 1}, {"a": 2}], 50)

    assert len(items) == 2
    assert is_complete is True


def test_trim_overfetched_incomplete_when_extra_row() -> None:
    rows = [{"id": index} for index in range(51)]
    items, is_complete = trim_overfetched(rows, 50)

    assert len(items) == 50
    assert is_complete is False


def test_build_operational_pagination_marks_incomplete() -> None:
    payload = build_operational_pagination(
        limit=50,
        offset=0,
        returned=50,
        is_complete=False,
    )

    assert payload == {
        "limit": 50,
        "offset": 0,
        "returned": 50,
        "is_complete": False,
    }
