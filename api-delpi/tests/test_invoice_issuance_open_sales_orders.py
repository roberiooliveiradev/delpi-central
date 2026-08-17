"""Pedidos de venda em aberto no wizard de emissão."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.application.use_cases.invoice_issuance.invoice_issuance_use_cases import (
    ListInvoiceIssuanceOpenSalesOrdersUseCase,
)
from app.domain.services.invoice_issuance.exceptions import InvoiceIssuanceValidationError
from app.domain.services.invoice_issuance.open_sales_orders import (
    group_open_sales_orders,
    split_product_label,
)


def test_split_product_label_code_and_description() -> None:
    assert split_product_label("90260001 Conector") == ("90260001", "Conector")
    assert split_product_label("90A") == ("90A", "90A")
    assert split_product_label("  ") == ("", "")


def test_group_open_sales_orders_filters_branch_and_zero_balance() -> None:
    orders = group_open_sales_orders(
        [
            {
                "filial": "01",
                "pedido": "000111",
                "linha": "01",
                "produto": "90260001 Conector",
                "pedido_cliente": "PC-9",
                "quantidade": 10,
                "entregue": 4,
                "saldo": 6,
                "preco_venda": 12.5,
                "valor_aberto": 75,
                "no_estoque": 20,
            },
            {
                "filial": "01",
                "pedido": "000111",
                "linha": "02",
                "produto": "90260002",
                "pedido_cliente": "PC-9",
                "quantidade": 2,
                "entregue": 2,
                "saldo": 0,
                "preco_venda": 8,
                "valor_aberto": 0,
                "no_estoque": 0,
            },
            {
                "filial": "02",
                "pedido": "000222",
                "linha": "01",
                "produto": "90260001 Outro",
                "saldo": 3,
                "preco_venda": 1,
                "valor_aberto": 3,
                "no_estoque": 0,
            },
        ],
        branch_code="01",
    )
    assert len(orders) == 1
    assert orders[0]["sales_order"] == "000111"
    assert orders[0]["lines_count"] == 1
    assert orders[0]["open_quantity"] == 6
    assert orders[0]["customer_order_number"] == "PC-9"
    line = orders[0]["lines"][0]
    assert line["product_code"] == "90260001"
    assert line["product_description"] == "Conector"
    assert line["quantity_open"] == 6
    assert line["unit_price"] == 12.5


def test_list_open_sales_orders_use_case_groups_customer_lines() -> None:
    class FakePva:
        def execute_for_customer(self, code: str, store: str):
            assert code == "000001"
            assert store == "01"
            return SimpleNamespace(
                items=[
                    {
                        "filial": "01",
                        "pedido": "000333",
                        "linha": "01",
                        "produto": "90260001",
                        "saldo": 2,
                        "preco_venda": 10,
                        "valor_aberto": 20,
                        "quantidade": 2,
                        "entregue": 0,
                        "no_estoque": 5,
                    }
                ]
            )

    data = ListInvoiceIssuanceOpenSalesOrdersUseCase(FakePva()).execute(
        branch_code="01", party_code="000001", party_store="01"
    )
    assert data["orders_count"] == 1
    assert data["lines_count"] == 1
    assert data["orders"][0]["sales_order"] == "000333"


def test_list_open_sales_orders_requires_customer() -> None:
    class FakePva:
        def execute_for_customer(self, code: str, store: str):
            raise AssertionError("não deveria consultar TOTVS")

    with pytest.raises(InvoiceIssuanceValidationError):
        ListInvoiceIssuanceOpenSalesOrdersUseCase(FakePva()).execute(
            branch_code="01", party_code=" ", party_store="01"
        )
