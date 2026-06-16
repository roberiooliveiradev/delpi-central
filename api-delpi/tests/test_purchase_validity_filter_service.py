from app.domain.services.production.purchase_validity_filter_service import (
    PurchaseValidityFilterService,
)


def test_valid_purchase_filter_excludes_internal_suppliers_and_transport_names():
    sql = PurchaseValidityFilterService.valid_purchase_filter_sql()

    assert "D1_FORNECE NOT IN (?, ?)" in sql
    assert "UPPER(SA2.A2_NOME) NOT LIKE '%TRANSP%'" in sql


def test_valid_purchase_filter_excludes_zero_quantity_freight_lines():
    sql = PurchaseValidityFilterService.valid_purchase_filter_sql()

    assert "SD1.D1_QUANT > 0" in sql


def test_supplier_filter_params_match_internal_supplier_codes():
    assert PurchaseValidityFilterService.supplier_filter_params() == [
        "000019",
        "001149",
    ]
