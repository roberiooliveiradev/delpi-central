"""Validation of the settlements query request DTO."""

from __future__ import annotations

import pytest

from app.application.dto.financeiro_settlements.settlements_request import (
    SettlementsQueryRequest,
)


def test_from_query_normalizes_filters() -> None:
    request = SettlementsQueryRequest.from_query(
        start_date="2026-01-01",
        end_date="2026-01-31",
        nature_code=" 100 ",
        movement_type=" BA ",
        sort_by="NATURE",
        sort_dir="ASC",
        page=2,
        page_size=100,
    )
    assert request.nature_code == "100"
    assert request.movement_type == "BA"
    assert request.sort_by == "nature"
    assert request.sort_dir == "asc"
    assert request.page == 2
    assert request.page_size == 100
    assert request.resolve_protheus_period() == ("20260101", "20260131")


def test_missing_period_rejected() -> None:
    with pytest.raises(ValueError):
        SettlementsQueryRequest.from_query(
            start_date=None, end_date="2026-01-31"
        )
    with pytest.raises(ValueError):
        SettlementsQueryRequest.from_query(
            start_date="2026-01-01", end_date=None
        )


def test_inverted_period_rejected() -> None:
    with pytest.raises(ValueError):
        SettlementsQueryRequest.from_query(
            start_date="2026-02-01", end_date="2026-01-01"
        )


def test_invalid_date_rejected() -> None:
    with pytest.raises(ValueError):
        SettlementsQueryRequest.from_query(
            start_date="not-a-date", end_date="2026-01-31"
        )


def test_invalid_sort_rejected() -> None:
    with pytest.raises(ValueError):
        SettlementsQueryRequest.from_query(
            start_date="2026-01-01",
            end_date="2026-01-31",
            sort_by="amount; DROP TABLE",
        )
    with pytest.raises(ValueError):
        SettlementsQueryRequest.from_query(
            start_date="2026-01-01",
            end_date="2026-01-31",
            sort_dir="sideways",
        )


def test_empty_filters_become_none_and_page_floor() -> None:
    request = SettlementsQueryRequest.from_query(
        start_date="2026-01-01",
        end_date="2026-01-31",
        nature_code="   ",
        movement_type="",
        page=0,
    )
    assert request.nature_code is None
    assert request.movement_type is None
    assert request.page == 1
