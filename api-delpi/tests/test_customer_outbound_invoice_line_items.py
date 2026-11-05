"""Contrato fiscal lote — filtros filial/cliente/loja, unidade D2_UM e quantidade decimal."""

from __future__ import annotations

from app.application.use_cases.pedidos_venda_abertos.list_customer_outbound_invoice_line_items_use_case import (
    ListCustomerOutboundInvoiceLineItemsUseCase,
)
from app.infrastructure.persistence.totvs.pedidos_venda_abertos.customer_outbound_invoice_line_items_sql import (
    line_items_sql,
)


def test_sql_requires_branch_customer_store_and_excludes_returns() -> None:
    sql = line_items_sql(product_count=2, exclude_returns=True)
    assert "D2_FILIAL" in sql
    assert "D2_CLIENTE" in sql
    assert "D2_LOJA" in sql
    assert "SF2010" in sql
    assert "F2_TIPO" in sql
    assert "<> 'D'" in sql
    assert "CONVERT(FLOAT" not in sql.upper()
    assert "CONVERT(VARCHAR" in sql.upper()
    assert "D2.D2_UM" in sql
    assert "invoice_unit" in sql
    assert "catalog_unit" in sql
    assert "B1_FILIAL = D2.D2_FILIAL" in sql
    assert sql.count("?") == 5 + 2  # branch,cliente,loja,start,end + products


def test_use_case_aggregates_totals_as_decimal_strings() -> None:
    class FakeRepo:
        def list_line_items(self, **kwargs):
            assert kwargs["branch"] == "02"
            assert kwargs["customer_code"] == "000001"
            assert kwargs["customer_store"] == "09"
            return [
                {
                    "product_code": "9001",
                    "quantity": "100.5",
                    "invoice_unit": "UN",
                    "unit": "UN",
                    "catalog_unit": "UN",
                    "branch": "02",
                    "invoice_number": "1",
                    "invoice_series": "1",
                    "item": "01",
                    "is_return": False,
                },
                {
                    "product_code": "9001",
                    "quantity": "50",
                    "invoice_unit": "UN",
                    "unit": "UN",
                    "catalog_unit": "UN",
                    "branch": "02",
                    "invoice_number": "2",
                    "invoice_series": "1",
                    "item": "01",
                    "is_return": False,
                },
                {
                    "product_code": "9001",
                    "quantity": "10",
                    "invoice_unit": "UN",
                    "unit": "UN",
                    "catalog_unit": "UN",
                    "branch": "02",
                    "invoice_number": "3",
                    "invoice_series": "1",
                    "item": "01",
                    "is_return": True,
                },
            ]

    result = ListCustomerOutboundInvoiceLineItemsUseCase(repository=FakeRepo()).execute(
        branch="02",
        customer_code="000001",
        customer_store="09",
        issue_date_start="2026-10-01",
        issue_date_end="2026-11-04",
        product_codes=["9001"],
        exclude_returns=True,
    )
    assert result["totals_by_product"] == [
        {
            "product_code": "9001",
            "quantity": "150.5",
            "unit": "UN",
            "comparable": True,
            "incompatibility_reason": None,
        }
    ]
    assert result["side_effects"] is False
    assert "Não prova reconhecimento" in result["coverage"]["limitations"][0]


def test_use_case_dedups_duplicate_sb1_join_rows() -> None:
    class FakeRepo:
        def list_line_items(self, **kwargs):
            base = {
                "product_code": "9001",
                "quantity": "10",
                "invoice_unit": "UN",
                "unit": "UN",
                "catalog_unit": "UN",
                "branch": "02",
                "invoice_number": "100",
                "invoice_series": "1",
                "item": "01",
                "is_return": False,
            }
            return [dict(base), dict(base)]  # mesma identidade fiscal

    result = ListCustomerOutboundInvoiceLineItemsUseCase(repository=FakeRepo()).execute(
        branch="02",
        customer_code="000001",
        customer_store="09",
        issue_date_start="2026-11-01",
        issue_date_end="2026-11-03",
        product_codes=["9001"],
    )
    assert result["returned_item_count"] == 1
    assert result["totals_by_product"][0]["quantity"] == "10"


def test_use_case_marks_incompatible_unit() -> None:
    class FakeRepo:
        def list_line_items(self, **kwargs):
            return [
                {
                    "product_code": "9001",
                    "quantity": "10",
                    "invoice_unit": "KG",
                    "unit": "KG",
                    "catalog_unit": "UN",
                    "branch": "02",
                    "invoice_number": "1",
                    "invoice_series": "1",
                    "item": "01",
                    "is_return": False,
                }
            ]

    result = ListCustomerOutboundInvoiceLineItemsUseCase(repository=FakeRepo()).execute(
        branch="02",
        customer_code="000001",
        customer_store="09",
        issue_date_start="2026-11-01",
        issue_date_end="2026-11-03",
        product_codes=["9001"],
    )
    row = result["totals_by_product"][0]
    assert row["comparable"] is False
    assert row["unit"] == "KG"
    assert row["incompatibility_reason"]


def test_use_case_rejects_other_branch() -> None:
    try:
        ListCustomerOutboundInvoiceLineItemsUseCase(repository=object()).execute(  # type: ignore[arg-type]
            branch="99",
            customer_code="000001",
            customer_store="09",
            issue_date_start="2026-10-01",
            issue_date_end="2026-11-04",
            product_codes=["9001"],
        )
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "branch" in str(exc).lower()
