"""Contrato fiscal lote — filtros, D2_UM, normalização MI→UN e quantidade decimal."""

from __future__ import annotations

from decimal import Decimal

from app.application.use_cases.pedidos_venda_abertos.list_customer_outbound_invoice_line_items_use_case import (
    ListCustomerOutboundInvoiceLineItemsUseCase,
)
from app.domain.services.pedidos_venda_abertos.fiscal_quantity_to_un import (
    convert_fiscal_quantity_to_un,
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


def test_ac01_one_mi_equals_1000_un() -> None:
    result = convert_fiscal_quantity_to_un(quantity="1", unit="MI")
    assert result.comparable is True
    assert result.quantity_un == Decimal("1000")
    assert result.conversion_factor == Decimal("1000")
    assert result.original_unit == "MI"


def test_ac02_fractional_mi_uses_decimal() -> None:
    result = convert_fiscal_quantity_to_un(quantity="0.125", unit="MI")
    assert result.quantity_un == Decimal("125")
    assert isinstance(result.quantity_un, Decimal)


def test_ac06_un_unchanged() -> None:
    result = convert_fiscal_quantity_to_un(quantity="150", unit="UN")
    assert result.quantity_un == Decimal("150")
    assert result.conversion_factor == Decimal("1")


def test_ac08_unknown_unit_not_comparable() -> None:
    result = convert_fiscal_quantity_to_un(quantity="10", unit="KG")
    assert result.comparable is False
    assert result.quantity_un is None
    assert result.incompatibility_reason


def test_ac09_invalid_quantity_not_silent_zero() -> None:
    result = convert_fiscal_quantity_to_un(quantity="abc", unit="MI")
    assert result.comparable is False
    assert result.quantity_un is None
    assert result.original_quantity is None
    assert "zero" in (result.incompatibility_reason or "").lower()


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
    row = result["totals_by_product"][0]
    assert row["quantity"] == "150.5"
    assert row["unit"] == "UN"
    assert row["quantity_un"] == "150.5"
    assert row["normalized_unit"] == "UN"
    assert row["comparable"] is True
    assert row["incompatibility_reason"] is None
    assert result["side_effects"] is False
    assert "Não prova reconhecimento" in result["coverage"]["limitations"][0]


def test_ac03_preserves_original_mi_and_normalized_un() -> None:
    class FakeRepo:
        def list_line_items(self, **kwargs):
            return [
                {
                    "product_code": "9001",
                    "quantity": "2.5",
                    "invoice_unit": "MI",
                    "unit": "MI",
                    "catalog_unit": "",
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
    item = result["items"][0]
    assert item["quantity"] == "2.5"
    assert item["unit"] == "MI"
    assert item["quantity_un"] == "2500"
    assert item["conversion_factor"] == "1000"
    assert item["comparable"] is True
    total = result["totals_by_product"][0]
    assert total["quantity"] == "2.5"
    assert total["unit"] == "MI"
    assert total["quantity_un"] == "2500"
    assert total["comparable"] is True


def test_ac07_mixed_mi_and_un_aggregates_after_per_item_normalization() -> None:
    class FakeRepo:
        def list_line_items(self, **kwargs):
            return [
                {
                    "product_code": "9001",
                    "quantity": "2",
                    "invoice_unit": "MI",
                    "unit": "MI",
                    "catalog_unit": "",
                    "branch": "02",
                    "invoice_number": "A",
                    "invoice_series": "1",
                    "item": "01",
                    "is_return": False,
                },
                {
                    "product_code": "9001",
                    "quantity": "500",
                    "invoice_unit": "UN",
                    "unit": "UN",
                    "catalog_unit": "",
                    "branch": "02",
                    "invoice_number": "B",
                    "invoice_series": "1",
                    "item": "01",
                    "is_return": False,
                },
            ]

    result = ListCustomerOutboundInvoiceLineItemsUseCase(repository=FakeRepo()).execute(
        branch="02",
        customer_code="000001",
        customer_store="09",
        issue_date_start="2026-11-01",
        issue_date_end="2026-11-03",
        product_codes=["9001"],
    )
    total = result["totals_by_product"][0]
    assert total["quantity_un"] == "2500"
    assert set(total["original_units"]) == {"MI", "UN"}
    assert total["quantity"] is None  # não misturar brutos
    assert total["comparable"] is True


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
    assert result["totals_by_product"][0]["quantity_un"] == "10"


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
    assert row["quantity_un"] is None
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
