from app.application.dto.supplies.get_purchase_order_otd_panel_request import (
    GetPurchaseOrderOtdPanelRequest,
)
from app.domain.totvs.protheus_product_types import PRODUCT_TYPE_RAW_MATERIAL
from app.infrastructure.persistence.totvs.supplies_repositories.purchase_order_otd_sql import (
    build_purchase_order_otd_filters,
    build_purchase_order_otd_lines_count_sql,
    build_purchase_order_otd_lines_list_sql,
    build_purchase_order_otd_sql,
    _list_order_clause,
)


def test_filters_force_mp_and_receipt_date_period() -> None:
    where_clause, params = build_purchase_order_otd_filters(
        branch="01",
        start_date="2026-07-01",
        end_date="2026-07-31",
    )

    assert "RTRIM(TIPO_PRODUTO) = ?" in where_clause
    assert "FILIAL = ?" in where_clause
    assert "DT_DIGITACAO" in where_clause
    assert params[0] == PRODUCT_TYPE_RAW_MATERIAL
    assert "01" in params


def test_kpi_sql_uses_dias_and_nolock_view() -> None:
    sql = build_purchase_order_otd_sql(where_clause="1=1")

    assert "VW_PONTUALIDADE_FORNECEDORES" in sql
    assert "WITH (NOLOCK)" in sql
    assert "DIAS >= 0" in sql
    assert "purchase_order_otd_pct" in sql


def test_panel_count_supports_late_status() -> None:
    sql = build_purchase_order_otd_lines_count_sql(
        where_clause="1=1",
        status="late",
    )

    assert "LINHAS_ELEGIVEIS" in sql
    assert "WHERE status = 'late'" in sql


def test_panel_list_orders_and_paginates() -> None:
    request = GetPurchaseOrderOtdPanelRequest(
        sort_by="days_diff",
        sort_dir="desc",
        page=1,
        page_size=20,
    )
    sql = build_purchase_order_otd_lines_list_sql(
        where_clause="1=1",
        request=request,
    )

    assert "OFFSET ? ROWS FETCH NEXT ? ROWS ONLY" in sql
    assert "ORDER BY days_diff DESC" in sql


def test_panel_list_includes_supplier_short_name_from_sa2() -> None:
    request = GetPurchaseOrderOtdPanelRequest(page=1, page_size=20)
    sql = build_purchase_order_otd_lines_list_sql(where_clause="1=1", request=request)

    assert "SA2010" in sql
    assert "A2_NREDUZ" in sql
    assert "supplier_short_name" in sql
    assert "COALESCE" in sql


def test_default_order_clause() -> None:
    clause = _list_order_clause(GetPurchaseOrderOtdPanelRequest())
    assert "status DESC" in clause
    assert "expected_delivery_date DESC" in clause
