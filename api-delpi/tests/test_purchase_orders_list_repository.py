from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock, patch

from app.infrastructure.persistence.totvs.supplies_repositories.purchase_orders_list_repository import (
    PurchaseOrdersListRepository,
    empty_purchase_orders_summary,
)
from app.infrastructure.persistence.totvs.supplies_repositories.purchase_orders_list_sql import (
    bind_purchase_orders_summary_params,
    split_sql_placeholder_counts,
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
    select_q, _where_q = split_sql_placeholder_counts(summary_sql)
    assert summary_params[:select_q] == ("20260911",) * select_q
    # Dates bind in SELECT buckets first — the previous bug appended them last.
    assert summary_params[0] == "20260911"
    assert summary_params[1] == "20260911"
    assert summary_params[2] == "01"
    assert list(summary_params).count("20260911") == 2


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
    assert summary_params[:2] == ("20260911", "20260911")
    assert "ABC" in summary_params[2:]
    assert "OFFSET" not in summary_sql


@patch.object(PurchaseOrdersListRepository, "execute_query")
@patch.object(PurchaseOrdersListRepository, "execute_one")
def test_summary_bind_order_regression_branch_01_reference_20260916(
    mock_execute_one: MagicMock,
    mock_execute_query: MagicMock,
) -> None:
    """Reproduces the Hero=0 bug: dates must bind before WHERE branch params."""
    mock_execute_one.side_effect = [
        {"total": 261},
        {
            "total_lines": 261,
            "total_open_value": 1000.0,
            "late_lines": 10,
            "on_time_lines": 240,
            "no_date_lines": 11,
        },
    ]
    mock_execute_query.return_value = []

    result = _opened_repo().list_open_lines(
        branch="01",
        late_only=False,
        page=1,
        page_size=50,
        reference=date(2026, 9, 16),
    )

    assert result["total"] == 261
    assert result["summary"]["total_lines"] == 261
    assert result["summary"]["total_lines"] > 0
    assert result["total"] == result["summary"]["total_lines"]

    _count_sql, count_params = mock_execute_one.call_args_list[0].args
    summary_sql, summary_params = mock_execute_one.call_args_list[1].args
    assert count_params[0] == "01"
    expected = bind_purchase_orders_summary_params(
        summary_sql,
        ["01"],
        today_protheus="20260916",
    )
    assert summary_params == expected
    assert summary_params[:2] == ("20260916", "20260916")
    assert summary_params[2] == "01"
    # Wrong historical order would put the branch code into date buckets.
    assert summary_params != ("01", "20260916", "20260916")


@patch.object(PurchaseOrdersListRepository, "execute_query")
@patch.object(PurchaseOrdersListRepository, "execute_one")
def test_late_only_list_total_matches_late_lines_not_total_lines(
    mock_execute_one: MagicMock,
    mock_execute_query: MagicMock,
) -> None:
    mock_execute_one.side_effect = [
        {"total": 10},
        {
            "total_lines": 40,
            "total_open_value": 99,
            "late_lines": 10,
            "on_time_lines": 25,
            "no_date_lines": 5,
        },
    ]
    mock_execute_query.return_value = []

    result = _opened_repo().list_open_lines(
        branches=["01", "02"],
        late_only=True,
        reference=date(2026, 9, 16),
    )
    assert result["total"] == 10
    assert result["total"] == result["summary"]["late_lines"]
    assert result["summary"]["total_lines"] == 40


@patch.object(PurchaseOrdersListRepository, "execute_query")
def test_export_open_lines_has_no_pagination_params(
    mock_execute_query: MagicMock,
) -> None:
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
    result = _opened_repo().export_open_lines(
        branches=["01", "02"],
        sort_by="open_value",
        sort_dir="desc",
        reference=date(2026, 9, 16),
    )
    assert result["total"] == 1
    sql, params = mock_execute_query.call_args.args
    assert "OFFSET" not in sql
    assert "FETCH" not in sql
    assert list(params) == ["01", "02"]
    assert "DESC" in sql
