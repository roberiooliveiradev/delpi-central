"""Testes do use case de carteira de pedidos em aberto do produto."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

from app.application.dto.product.get_product_sales_open_orders_request import (
    GetProductSalesOpenOrdersRequest,
)
from app.application.use_cases.product.get_product_sales_open_orders_use_case import (
    GetProductSalesOpenOrdersUseCase,
)
from app.domain.entities.product.product_sales_open_orders import ProductSalesOpenOrders


def test_open_orders_use_case_returns_items_and_summary() -> None:
    repository = MagicMock()
    repository.get_sales_open_orders.return_value = ProductSalesOpenOrders(
        items=[
            {
                "branch": "01",
                "order_number": "000123",
                "customer_name": "ACME",
                "open_quantity": 16.0,
                "open_value": 9202.08,
            }
        ],
        quantity=16.0,
        value=9202.08,
        orders=1,
        page=1,
        page_size=50,
        total=1,
        total_pages=1,
    )
    use_case = GetProductSalesOpenOrdersUseCase(repository=repository)

    payload = use_case.execute(
        GetProductSalesOpenOrdersRequest(code="90262910", branch="01")
    )

    repository.get_sales_open_orders.assert_called_once_with(
        code="90262910",
        branch="01",
        page=1,
        page_size=50,
    )
    assert payload["orders"] == 1
    assert payload["summary"]["quantity"] == 16.0
    assert len(payload["items"]) == 1
    assert payload["items"][0]["order_number"] == "000123"


def test_open_orders_repository_sql_includes_branch_and_items() -> None:
    from app.infrastructure.persistence.totvs.product_repositories.product_sales_open_orders_repository import (
        ProductSalesOpenOrdersRepository,
    )

    repo = ProductSalesOpenOrdersRepository()
    captured: dict = {}

    def fake_enter(self):
        return self

    def fake_exit(self, *args):
        return False

    def fake_one(sql, params=()):
        captured["summary_sql"] = sql
        captured["summary_params"] = params
        return {
            "open_quantity": 16.0,
            "open_value": 9202.08,
            "orders": 1,
            "line_count": 1,
        }

    def fake_query(sql, params=()):
        captured["items_sql"] = sql
        captured["items_params"] = params
        return [
            {
                "branch": "01",
                "order_number": "000123",
                "order_item": "01",
                "customer_code": "000001",
                "customer_store": "01",
                "customer_name": "ACME",
                "open_quantity": 16.0,
                "unit_price": 575.13,
                "open_value": 9202.08,
                "delivery_date": "2026-09-30",
                "issue_date": "2026-08-01",
            }
        ]

    repo.__enter__ = fake_enter.__get__(repo, ProductSalesOpenOrdersRepository)
    repo.__exit__ = fake_exit.__get__(repo, ProductSalesOpenOrdersRepository)
    repo.execute_one = fake_one
    repo.execute_query = fake_query

    result = repo.get_sales_open_orders("90262910", branch="01", page=1, page_size=50)

    assert "C6.C6_FILIAL = ?" in captured["summary_sql"]
    assert captured["summary_params"] == ("90262910", "01")
    assert "ORDER BY" in captured["items_sql"]
    assert result.orders == 1
    assert result.items[0]["order_number"] == "000123"
