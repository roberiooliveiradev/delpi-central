from __future__ import annotations

from app.application.dto.third_party_materials.query_request import (
    ThirdPartyMaterialsQueryRequest,
)
from app.infrastructure.persistence.totvs.third_party_materials.third_party_materials_sql import (
    VIEW,
    build_count_shipments_sql,
    build_details_by_recno_sql,
    build_details_by_recnos_sql,
    build_export_sql,
    build_filter_clause,
    build_shipment_page_sql,
    build_summary_sql,
)


def _request(**overrides) -> ThirdPartyMaterialsQueryRequest:
    payload = {
        "branch": "01",
        "product": "10211413",
        "only_with_balance": False,
        "include_test_products": False,
        "page": 1,
        "page_size": 20,
    }
    payload.update(overrides)
    return ThirdPartyMaterialsQueryRequest.from_query(**payload)


def test_view_name_and_decimal_cast_are_stable() -> None:
    assert VIEW == "dbo.VW_PD3_BENEF_RETORNOS"
    sql, _ = build_summary_sql(_request())
    assert "decimal(28, 8)" in sql
    assert "DISTINCT" in sql
    assert "RECNO_REMESSA" in sql


def test_filter_is_parameterized_and_requires_branch() -> None:
    where_sql, params = build_filter_clause(_request(product="10211413", status="partial"))
    assert "FILIAL)) = ?" in where_sql
    assert "PRODUTO)) = ?" in where_sql
    assert "STATUS_REMESSA = ?" in where_sql
    assert params == ["01", "10211413", "PARCIAL", "99999999"]
    assert "B6_TPCF" not in where_sql
    assert "%s" not in where_sql
    assert "'" + "10211413" + "'" not in where_sql


def test_customer_reference_filter_joins_sb1_and_is_parameterized() -> None:
    where_sql, params = build_filter_clause(
        _request(product=None, customer_reference="10018137")
    )
    assert "B1_REFEREN" in where_sql
    assert "Latin1_General_CI_AI" in where_sql
    assert params == ["01", "10018137%", "99999999"]
    count_sql, _ = build_count_shipments_sql(_request(customer_reference="10018137"))
    assert "SB1010 SB1" in count_sql
    assert "REFERENCIA_CLIENTE" in count_sql or "B1_REFEREN" in count_sql
    details_sql, _ = build_details_by_recnos_sql([1])
    assert "REFERENCIA_CLIENTE" in details_sql
    assert "SB1010 SB1" in details_sql


def test_ignored_products_can_be_included() -> None:
    where_sql, params = build_filter_clause(_request(include_test_products=True))
    assert "NOT IN" not in where_sql
    assert params == ["01", "10211413"]


def test_pagination_is_two_step_by_recno() -> None:
    count_sql, count_params = build_count_shipments_sql(_request())
    page_sql, page_params = build_shipment_page_sql(_request(page=2, page_size=10))
    assert "COUNT(*)" in count_sql
    assert "DISTINCT V.RECNO_REMESSA" in count_sql
    assert count_params[0] == "01"
    assert "OFFSET ? ROWS FETCH NEXT ? ROWS ONLY" in page_sql
    assert page_params[-2:] == (10, 10)


def test_details_in_list_uses_placeholders() -> None:
    sql, params = build_details_by_recnos_sql([1, 2, 3])
    assert "V.RECNO_REMESSA IN (?, ?, ?)" in sql
    assert params == (1, 2, 3)
    assert "B6_TPCF" not in sql
    assert "TIPO_PARCEIRO_RETORNO" in sql
    assert "COD_PARCEIRO_RETORNO" not in sql
    assert "LOJA_PARCEIRO_RETORNO" not in sql


def test_single_recno_query_filters_branch() -> None:
    sql, params = build_details_by_recno_sql(
        shipment_recno=27062725,
        branch="01",
        ignored_products=("99999999",),
    )
    assert "V.RECNO_REMESSA = ?" in sql
    assert params == (27062725, "01", "99999999")


def test_export_uses_top_placeholder() -> None:
    sql, params = build_export_sql(_request(), limit=500)
    assert "SELECT TOP (?)" in sql
    assert params[0] == 500
