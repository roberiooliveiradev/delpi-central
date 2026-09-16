from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock, patch

from app.infrastructure.persistence.totvs.supplies_repositories.purchase_orders_list_repository import (
    PurchaseOrdersListRepository,
    empty_purchase_orders_summary,
)


def _opened_repo() -> PurchaseOrdersListRepository:
    repo = PurchaseOrdersListRepository()
    repo.connection = object()
    repo.cursor = object()
    repo._connect = lambda: None  # type: ignore[method-assign]
    repo._close = lambda *a, **k: None  # type: ignore[method-assign]
    return repo


@patch.object(PurchaseOrdersListRepository, "execute_query")
@patch.object(PurchaseOrdersListRepository, "execute_one")
def test_list_open_lines_includes_summary_and_items(
    mock_execute_one: MagicMock,
    mock_execute_query: MagicMock,
) -> None:
    mock_execute_one.side_effect = [
        {"total": 2},
        {
            "total_lines": 5,
            "total_open_value": 1500.5,
            "late_lines": 2,
            "on_time_lines": 2,
            "no_date_lines": 1,
        },
    ]
    mock_execute_query.return_value = [
        {
            "branch": "01",
            "order_number": "0001",
            "order_item": "0001",
            "product_code": "P1",
            "product_description": "Item",
            "ordered_quantity": 10,
            "delivered_quantity": 2,
            "open_quantity": 8,
            "issue_date": "20260101",
            "expected_delivery_date": "20260901",
            "supplier_code": "F1",
            "supplier_store": "01",
            "supplier_name": "Fornecedor",
            "unit_price": 10,
            "open_value": 80,
        }
    ]

    result = _opened_repo().list_open_lines(
        branch="01",
        late_only=True,
        page=1,
        page_size=50,
        reference=date(2026, 9, 11),
    )

    assert result["total"] == 2
    assert len(result["items"]) == 1
    assert result["summary"]["total_lines"] == 5
    assert result["summary"]["total_open_value"] == 1500.5
    assert result["summary"]["late_lines"] == 2
    assert result["summary"]["on_time_lines"] == 2
    assert result["summary"]["no_date_lines"] == 1
    assert (
        result["summary"]["total_lines"]
        == result["summary"]["late_lines"]
        + result["summary"]["on_time_lines"]
        + result["summary"]["no_date_lines"]
    )
    assert result["total"] != result["summary"]["total_lines"]

    assert mock_execute_one.call_count == 2
    summary_sql, summary_params = mock_execute_one.call_args_list[1].args
    assert "OFFSET" not in summary_sql
    assert "total_lines" in summary_sql
    assert summary_params[-2:] == ("20260911", "20260911")
    # Summary query params must not include late_only today predicate beyond bucket params.
    assert summary_params.count("20260911") == 2


@patch.object(PurchaseOrdersListRepository, "execute_query")
@patch.object(PurchaseOrdersListRepository, "execute_one")
def test_list_open_lines_zero_rows_returns_empty_summary(
    mock_execute_one: MagicMock,
    mock_execute_query: MagicMock,
) -> None:
    mock_execute_one.side_effect = [None, None]
    mock_execute_query.return_value = []

    result = _opened_repo().list_open_lines(branch="01", page=1, page_size=50)

    assert result["items"] == []
    assert result["total"] == 0
    assert result["summary"] == empty_purchase_orders_summary()


@patch.object(PurchaseOrdersListRepository, "execute_query")
@patch.object(PurchaseOrdersListRepository, "execute_one")
def test_list_open_lines_normalizes_numeric_summary(
    mock_execute_one: MagicMock,
    mock_execute_query: MagicMock,
) -> None:
    mock_execute_one.side_effect = [
        {"total": 0},
        {
            "total_lines": "3",
            "total_open_value": "99.9",
            "late_lines": "1",
            "on_time_lines": "1",
            "no_date_lines": "1",
        },
    ]
    mock_execute_query.return_value = []

    result = _opened_repo().list_open_lines(branch="01")
    summary = result["summary"]
    assert summary["total_lines"] == 3
    assert summary["total_open_value"] == 99.9
    assert isinstance(summary["total_open_value"], float)
    assert (
        summary["total_lines"]
        == summary["late_lines"] + summary["on_time_lines"] + summary["no_date_lines"]
    )


@patch.object(PurchaseOrdersListRepository, "execute_query")
@patch.object(PurchaseOrdersListRepository, "execute_one")
def test_summary_ignores_late_only_in_filter_params(
    mock_execute_one: MagicMock,
    mock_execute_query: MagicMock,
) -> None:
    mock_execute_one.side_effect = [
        {"total": 1},
        {
            "total_lines": 4,
            "total_open_value": 10,
            "late_lines": 1,
            "on_time_lines": 2,
            "no_date_lines": 1,
        },
    ]
    mock_execute_query.return_value = []

    _opened_repo().list_open_lines(
        branch="01",
        product_code="ABC",
        late_only=True,
        reference=date(2026, 9, 11),
    )

    count_sql, count_params = mock_execute_one.call_args_list[0].args
    summary_sql, summary_params = mock_execute_one.call_args_list[1].args
    assert "RTRIM(SC7.C7_DATPRF) < ?" in count_sql or "20260911" in count_params
    assert "ABC" in summary_params
    # Only the two bucket reference dates, not a third late_only filter date.
    assert list(summary_params).count("20260911") == 2
    assert "OFFSET" not in summary_sql
