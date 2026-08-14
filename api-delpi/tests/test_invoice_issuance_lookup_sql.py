"""SQL de lookups TOTVS — SA1 (CNPJ), SB1, saldo SB2 local 01 e SA4 (A4_NREDUZ)."""

from __future__ import annotations

import inspect

from app.domain.totvs.protheus_warehouses import WAREHOUSE_ALMOXARIFADO
from app.infrastructure.persistence.totvs.customer_repositories.customer_repository import (
    CustomerRepository,
)
from app.infrastructure.persistence.totvs.invoice_issuance_repositories import (
    totvs_invoice_issuance_lookup_repository as lookup_mod,
)
from app.infrastructure.persistence.totvs.invoice_issuance_repositories.totvs_invoice_issuance_lookup_repository import (
    TotvsInvoiceIssuanceLookupRepository,
)


def test_customer_search_includes_cnpj() -> None:
    source = inspect.getsource(TotvsInvoiceIssuanceLookupRepository.search_customers)
    assert "A1_CGC" in source
    assert "SA1010" in source
    assert "MSBLQL" in source


def test_customer_repository_delegates_cnpj_search() -> None:
    source = inspect.getsource(CustomerRepository.search_customers_by_query)
    assert "TotvsInvoiceIssuanceLookupRepository" in source
    assert "search_customers" in source


def test_product_search_uses_sb1() -> None:
    source = inspect.getsource(TotvsInvoiceIssuanceLookupRepository.search_products)
    assert "SB1010" in source
    assert "B1_COD" in source


def test_carrier_search_uses_sa4_nreduz() -> None:
    source = inspect.getsource(lookup_mod)
    method = inspect.getsource(TotvsInvoiceIssuanceLookupRepository.search_carriers)
    assert "SA4010" in method
    assert "A4_NREDUZ" in method
    assert "A4_COD" in method
    assert "A4_CGC" in method
    assert "A4_END" in source
    assert "A4_TEL" in source
    assert "A4_DDD" in source
    assert "A4_MSBLQL" not in source


def test_warehouse_balance_uses_almoxarifado_01() -> None:
    source = inspect.getsource(
        TotvsInvoiceIssuanceLookupRepository.get_warehouse_01_balance
    )
    assert "SB2010" in source
    assert "B2_LOCAL" in source
    assert WAREHOUSE_ALMOXARIFADO == "01"
