"""Smoke e unitários — /supplies/stock-balances."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.application.dto.supplies.stock_balances_request import (
    StockBalancesItemsRequest,
    StockBalancesQueryRequest,
)
from app.application.services.response_meta_builder import DATA_VERSION
from app.domain.totvs.protheus_branches import normalize_optional_branch_codes
from app.infrastructure.persistence.totvs.supplies_repositories import (
    stock_balances_sql as sql,
)


def _body(response) -> dict:
    return json.loads(response.content.decode())


@pytest.fixture
def stock_balances_client() -> TestClient:
    from fastapi import FastAPI

    from app.interface.http.routes.supplies.stock_balances_router import router

    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def test_router_exposes_summary_and_items(stock_balances_client: TestClient) -> None:
    from app.interface.http.routes.supplies.stock_balances_router import router

    paths = {route.path for route in router.routes if hasattr(route, "path")}
    assert router.prefix == "/supplies/stock-balances"
    assert "/supplies/stock-balances/summary" in paths
    assert "/supplies/stock-balances/items" in paths


def test_normalize_optional_branch_codes_single_and_multi() -> None:
    assert normalize_optional_branch_codes(None) == ()
    assert normalize_optional_branch_codes([]) == ()
    assert normalize_optional_branch_codes("all") == ()
    assert normalize_optional_branch_codes(["all"]) == ()
    assert normalize_optional_branch_codes("01") == ("01",)
    assert normalize_optional_branch_codes(["02"]) == ("02",)
    assert normalize_optional_branch_codes(["01", "02"]) == ("01", "02")
    assert normalize_optional_branch_codes(["02", "01"]) == ("01", "02")
    assert normalize_optional_branch_codes(["01", "01"]) == ("01",)


def test_normalize_optional_branch_codes_rejects_invalid_and_ambiguous() -> None:
    with pytest.raises(ValueError):
        normalize_optional_branch_codes(["03"])
    with pytest.raises(ValueError):
        normalize_optional_branch_codes(["all", "01"])
    with pytest.raises(ValueError):
        normalize_optional_branch_codes(["01", "all"])


def test_sql_valuation_uses_qatu_times_cm1_same_local() -> None:
    assert "B2_QATU" in sql.STOCK_VALUE_EXPR
    assert "B2_CM1" in sql.STOCK_VALUE_EXPR
    assert "AVG(" not in sql.STOCK_VALUE_EXPR.upper()
    where, params = sql.build_where_clause(
        branches=["01"],
        warehouse="50",
        only_positive=True,
    )
    assert "B2_FILIAL" in where
    assert "B2_LOCAL" in where
    assert "B2_QATU > 0" in where
    assert params == ["01", "50"]
    summary = sql.format_summary_sql(where)
    assert "AVG(" not in summary.upper()
    assert sql.STOCK_VALUE_EXPR in summary
    items = sql.format_items_sql(where, order_by=sql.resolve_order_by(None))
    assert "OFFSET ? ROWS FETCH NEXT ? ROWS ONLY" in items
    assert "SB1010" in items
    assert "B1_UM" in items
    assert "unit_of_measure" in items


def test_sql_multi_branch_uses_in_predicate_same_dataset() -> None:
    where, params = sql.build_where_clause(
        branches=["02", "01"],
        warehouse=None,
        only_positive=True,
    )
    assert "IN (?, ?)" in where
    assert params == ["01", "02"]
    assert "B2_QATU > 0" in where
    summary = sql.format_summary_sql(where)
    assert "COUNT(DISTINCT SB2.B2_COD)" in summary
    assert "COUNT(DISTINCT LTRIM(RTRIM(SB2.B2_LOCAL)))" in summary
    assert sql.STOCK_VALUE_EXPR in summary
    by_wh = sql.format_by_warehouse_sql(where)
    assert "GROUP BY LTRIM(RTRIM(SB2.B2_FILIAL)), LTRIM(RTRIM(SB2.B2_LOCAL))" in by_wh


def test_sql_legacy_no_branch_and_only_positive_false() -> None:
    where_legacy, params_legacy = sql.build_where_clause(
        branches=(),
        warehouse=None,
        only_positive=True,
    )
    assert "B2_FILIAL" not in where_legacy
    assert params_legacy == []
    assert "B2_QATU > 0" in where_legacy

    where_all_balances, params_all = sql.build_where_clause(
        branches=["01"],
        warehouse=None,
        only_positive=False,
    )
    assert "B2_QATU > 0" not in where_all_balances
    assert params_all == ["01"]


def test_request_default_only_positive_true() -> None:
    assert StockBalancesQueryRequest().only_positive is True
    assert StockBalancesItemsRequest().only_positive is True
    assert StockBalancesQueryRequest(branches=["01"]).branches == ("01",)


def test_summary_parses_execute_query_multiple_shape() -> None:
    """execute_query_multiple returns [{data: rows}, ...] — not bare lists."""
    from app.infrastructure.persistence.totvs.supplies_repositories.stock_balances_query_repository import (
        StockBalancesQueryRepository,
    )

    repo = StockBalancesQueryRepository()
    fake = MagicMock()
    fake.execute_query_multiple.return_value = [
        {
            "index": 1,
            "data": [
                {
                    "product_count": 4,
                    "total_quantity": 10,
                    "total_stock_value": 100.5,
                    "total_stock_value_vatu1": 100.5,
                    "warehouse_count": 1,
                }
            ],
        },
        {
            "index": 2,
            "data": [
                {
                    "branch": "01",
                    "warehouse": "50",
                    "product_count": 4,
                    "total_quantity": 10,
                    "total_stock_value": 100.5,
                    "total_stock_value_vatu1": 100.5,
                }
            ],
        },
    ]
    fake.__enter__.return_value = fake
    fake.__exit__.return_value = False

    with patch.object(StockBalancesQueryRepository, "__enter__", return_value=fake):
        with patch.object(StockBalancesQueryRepository, "__exit__", return_value=False):
            result = repo.fetch_summary(
                branches=["01"], warehouse="50", only_positive=True
            )

    assert result["summary"]["product_count"] == 4
    assert result["summary"]["total_stock_value"] == 100.5
    assert result["summary"]["branch"] == "01"
    assert result["by_warehouse"][0]["warehouse"] == "50"
    assert result["by_warehouse"][0]["branch"] == "01"


def test_fetch_items_maps_unit_of_measure_null_when_absent() -> None:
    from app.infrastructure.persistence.totvs.supplies_repositories.stock_balances_query_repository import (
        StockBalancesQueryRepository,
    )

    repo = StockBalancesQueryRepository()
    fake = MagicMock()
    fake.execute_query.return_value = [
        {
            "product_code": "10070821",
            "description": "CABO PP",
            "unit_of_measure": "PC",
            "branch": "01",
            "warehouse": "50",
            "quantity": 10,
            "unit_cost": 1.5,
            "stock_value": 15,
        },
        {
            "product_code": "99999999",
            "description": "SEM UM",
            "unit_of_measure": None,
            "branch": "01",
            "warehouse": "03",
            "quantity": 1,
            "unit_cost": 2,
            "stock_value": 2,
        },
        {
            "product_code": "88888888",
            "description": "UM VAZIA",
            "unit_of_measure": "   ",
            "branch": "02",
            "warehouse": "00",
            "quantity": 0,
            "unit_cost": 0,
            "stock_value": 0,
        },
    ]
    fake.__enter__.return_value = fake
    fake.__exit__.return_value = False

    with patch.object(StockBalancesQueryRepository, "__enter__", return_value=fake):
        with patch.object(StockBalancesQueryRepository, "__exit__", return_value=False):
            items = repo.fetch_items(
                branches=["01", "02"],
                warehouse=None,
                only_positive=False,
                sort="stock_value_desc",
                offset=0,
                page_size=50,
            )

    assert items[0]["unit_of_measure"] == "PC"
    assert items[1]["unit_of_measure"] is None
    assert items[2]["unit_of_measure"] is None
    assert items[1]["warehouse_label"] is None
    assert items[1]["warehouse"] == "03"


@patch(
    "app.interface.http.routes.supplies.stock_balances_router"
    ".build_get_supplies_stock_balances_summary_use_case"
)
def test_summary_returns_envelope(mock_builder, stock_balances_client: TestClient) -> None:
    use_case = MagicMock()
    use_case.execute.return_value = {
        "summary": {
            "branch": "01",
            "warehouse": "50",
            "product_count": 4,
            "total_quantity": 100.0,
            "total_stock_value": 52481.83,
            "total_stock_value_vatu1": 52481.83,
            "warehouse_count": 1,
            "valuation": "qatu_times_cm1_same_local",
        },
        "by_warehouse": [
            {
                "branch": "01",
                "warehouse": "50",
                "warehouse_label": "WIP / processo",
                "product_count": 4,
                "total_quantity": 100.0,
                "total_stock_value": 52481.83,
                "total_stock_value_vatu1": 52481.83,
            }
        ],
    }
    mock_builder.return_value = use_case

    response = stock_balances_client.get(
        "/supplies/stock-balances/summary",
        params={"branch": "01", "warehouse": "50"},
    )
    body = _body(response)

    assert response.status_code == 200
    assert body["success"] is True
    assert body["meta"]["operationId"] == "get_supplies_stock_balances_summary"
    assert body["meta"]["entity"] == "supplies_stock_balances_summary"
    assert body["meta"]["shape"] == "playbook_report"
    assert body["meta"]["dataVersion"] == DATA_VERSION
    assert body["data"]["summary"]["product_count"] == 4
    req = use_case.execute.call_args.args[0]
    assert req.branches == ("01",)
    assert req.only_positive is True


@patch(
    "app.interface.http.routes.supplies.stock_balances_router"
    ".build_get_supplies_stock_balances_items_use_case"
)
def test_items_returns_envelope(mock_builder, stock_balances_client: TestClient) -> None:
    use_case = MagicMock()
    use_case.execute.return_value = {
        "items": [
            {
                "product_code": "10070821",
                "description": "CABO PP",
                "unit_of_measure": "PC",
                "branch": "01",
                "warehouse": "50",
                "quantity": 10.0,
                "unit_cost": 1.5,
                "stock_value": 15.0,
            }
        ],
        "page": 1,
        "page_size": 50,
        "total": 1,
        "total_pages": 1,
        "sort": "stock_value_desc",
        "pagination": {
            "page": 1,
            "page_size": 50,
            "total": 1,
            "total_pages": 1,
            "is_complete": True,
        },
    }
    mock_builder.return_value = use_case

    response = stock_balances_client.get(
        "/supplies/stock-balances/items",
        params={"branch": "01", "warehouse": "50", "page": 1},
    )
    body = _body(response)

    assert response.status_code == 200
    assert body["meta"]["operationId"] == "get_supplies_stock_balances_items"
    assert body["meta"]["entity"] == "supplies_stock_balances_item"
    assert body["meta"]["shape"] == "paged_list"
    assert body["data"]["items"][0]["product_code"] == "10070821"
    assert body["meta"]["fields"]["unit_of_measure"]["label"] == "Unidade de medida"


@patch(
    "app.interface.http.routes.supplies.stock_balances_router"
    ".build_get_supplies_stock_balances_summary_use_case"
)
def test_summary_accepts_multi_branch_and_normalizes_order(
    mock_builder, stock_balances_client: TestClient
) -> None:
    use_case = MagicMock()
    use_case.execute.return_value = {"summary": {}, "by_warehouse": []}
    mock_builder.return_value = use_case

    response = stock_balances_client.get(
        "/supplies/stock-balances/summary",
        params=[("branch", "02"), ("branch", "01")],
    )
    assert response.status_code == 200
    req = use_case.execute.call_args.args[0]
    assert req.branches == ("01", "02")


@patch(
    "app.interface.http.routes.supplies.stock_balances_router"
    ".build_get_supplies_stock_balances_summary_use_case"
)
def test_summary_dedupes_duplicate_branch(
    mock_builder, stock_balances_client: TestClient
) -> None:
    use_case = MagicMock()
    use_case.execute.return_value = {"summary": {}, "by_warehouse": []}
    mock_builder.return_value = use_case

    response = stock_balances_client.get(
        "/supplies/stock-balances/summary",
        params=[("branch", "01"), ("branch", "01")],
    )
    assert response.status_code == 200
    req = use_case.execute.call_args.args[0]
    assert req.branches == ("01",)


@patch(
    "app.interface.http.routes.supplies.stock_balances_router"
    ".build_get_supplies_stock_balances_summary_use_case"
)
def test_summary_legacy_omitted_and_all(
    mock_builder, stock_balances_client: TestClient
) -> None:
    use_case = MagicMock()
    use_case.execute.return_value = {"summary": {}, "by_warehouse": []}
    mock_builder.return_value = use_case

    omitted = stock_balances_client.get("/supplies/stock-balances/summary")
    all_resp = stock_balances_client.get(
        "/supplies/stock-balances/summary", params={"branch": "all"}
    )
    assert omitted.status_code == 200
    assert all_resp.status_code == 200
    assert use_case.execute.call_args_list[0].args[0].branches == ()
    assert use_case.execute.call_args_list[1].args[0].branches == ()


def test_summary_rejects_invalid_branch(stock_balances_client: TestClient) -> None:
    response = stock_balances_client.get(
        "/supplies/stock-balances/summary",
        params={"branch": "03"},
    )
    assert response.status_code == 400


def test_summary_rejects_ambiguous_all_and_concrete(
    stock_balances_client: TestClient,
) -> None:
    response = stock_balances_client.get(
        "/supplies/stock-balances/summary",
        params=[("branch", "all"), ("branch", "01")],
    )
    assert response.status_code == 400


@patch(
    "app.interface.http.routes.supplies.stock_balances_router"
    ".build_get_supplies_stock_balances_summary_use_case"
)
def test_location_alias_maps_to_warehouse(
    mock_builder, stock_balances_client: TestClient
) -> None:
    use_case = MagicMock()
    use_case.execute.return_value = {"summary": {}, "by_warehouse": []}
    mock_builder.return_value = use_case

    response = stock_balances_client.get(
        "/supplies/stock-balances/summary",
        params={"location": "25"},
    )
    assert response.status_code == 200
    req = use_case.execute.call_args.args[0]
    assert req.warehouse == "25"


@patch(
    "app.interface.http.routes.supplies.stock_balances_router"
    ".build_get_supplies_stock_balances_items_use_case"
)
def test_items_accepts_page_size_500(
    mock_builder, stock_balances_client: TestClient
) -> None:
    """TV pode pedir até 500 linhas; limite anterior (200) gerava 422."""
    use_case = MagicMock()
    use_case.execute.return_value = {
        "items": [],
        "page": 1,
        "page_size": 500,
        "total": 0,
        "total_pages": 0,
        "sort": "stock_value_desc",
        "pagination": {
            "page": 1,
            "page_size": 500,
            "total": 0,
            "total_pages": 0,
            "is_complete": True,
        },
    }
    mock_builder.return_value = use_case

    response = stock_balances_client.get(
        "/supplies/stock-balances/items",
        params={
            "branch": "01",
            "warehouse": "25",
            "page": 1,
            "page_size": 500,
            "only_positive": True,
            "sort": "stock_value_desc",
        },
    )
    assert response.status_code == 200
    body = _body(response)
    assert body["meta"]["operationId"] == "get_supplies_stock_balances_items"
    req = use_case.execute.call_args.args[0]
    assert req.page_size == 500
    assert req.only_positive is True


@patch(
    "app.interface.http.routes.supplies.stock_balances_router"
    ".build_get_supplies_stock_balances_items_use_case"
)
def test_items_only_positive_false_reaches_request(
    mock_builder, stock_balances_client: TestClient
) -> None:
    use_case = MagicMock()
    use_case.execute.return_value = {
        "items": [],
        "page": 1,
        "page_size": 50,
        "total": 0,
        "total_pages": 0,
        "sort": "stock_value_desc",
        "pagination": {
            "page": 1,
            "page_size": 50,
            "total": 0,
            "total_pages": 0,
            "is_complete": True,
        },
    }
    mock_builder.return_value = use_case

    response = stock_balances_client.get(
        "/supplies/stock-balances/items",
        params={"branch": "01", "only_positive": False},
    )
    assert response.status_code == 200
    req = use_case.execute.call_args.args[0]
    assert req.only_positive is False


def test_items_rejects_page_size_over_500(stock_balances_client: TestClient) -> None:
    response = stock_balances_client.get(
        "/supplies/stock-balances/items",
        params={"page_size": 501},
    )
    assert response.status_code == 422
