"""Regression tests for supplier identity and consolidated SB6 pending balances."""
from __future__ import annotations

from decimal import Decimal
from io import BytesIO
from unittest.mock import MagicMock, patch

from openpyxl import load_workbook

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.application.dto.third_party_materials.query_request import ThirdPartyMaterialsQueryRequest
from app.application.use_cases.third_party_materials.pending_supplier_report_use_case import PendingSupplierReportUseCase
from app.infrastructure.persistence.totvs.third_party_materials.third_party_materials_sql import (
    build_details_by_recnos_sql,
    build_export_sql,
)
from app.infrastructure.persistence.totvs.third_party_materials.third_party_pending_sql import (
    build_pending_export_sql,
    build_pending_page_sql,
    build_pending_summary_sql,
)


def _request(**kwargs):
    return ThirdPartyMaterialsQueryRequest.from_query(
        branch="01", partner_code="001692", **kwargs
    )


def test_detail_uses_sa2_only_for_supplier_and_retains_sa1_for_customer():
    sql, params = build_details_by_recnos_sql([27066796])
    assert "LEFT JOIN SA2010 SA2" in sql
    assert "V.TIPO_PARCEIRO = 'F'" in sql
    assert "SA2.A2_NOME" in sql
    assert "ELSE V.NOME_PARCEIRO" in sql
    assert params == (27066796,)


def test_consolidated_query_groups_remessas_before_summing_and_is_parameterized():
    request = _request()
    summary_sql, params = build_pending_summary_sql(request)
    assert "GROUP BY V.RECNO_REMESSA" in summary_sql
    assert "GROUP BY supplier_code, supplier_store, product_code" in summary_sql
    assert "V.TIPO_PARCEIRO = 'F'" in summary_sql
    assert "V.POSSUI_SALDO = 'S'" in summary_sql
    assert "SA2010" not in summary_sql
    assert params == ("01", "001692", "99999999")

    page_sql, page_params = build_pending_page_sql(request)
    assert "LEFT JOIN SA2010 SA2" in page_sql
    assert "OFFSET ? ROWS FETCH NEXT ? ROWS ONLY" in page_sql
    assert page_params[-2:] == (0, 20)

    export_sql, export_params = build_pending_export_sql(request, limit=20000)
    assert "SELECT TOP (?)" in export_sql
    # The CTE WHERE is evaluated/bound before the final SELECT TOP (?).
    # Regresses an earlier reversal that surfaced as HTTP 503 on CSV/XLSX.
    assert export_sql.index("WHERE") < export_sql.index("SELECT TOP (?)")
    assert export_sql.count("?") == len(export_params)
    assert export_params[:-1] == params
    assert export_params[-1] == 20000


def test_export_markers_keep_filters_before_limit_with_multiple_fields():
    request = _request(product="20050012", partner_store="01")
    sql, params = build_pending_export_sql(request, limit=20000)

    assert sql.count("?") == len(params)
    assert params == ("01", "20050012", "001692", "01", "99999999", 20000)
    assert "SELECT TOP (?)" in sql
    assert sql.index("V.FILIAL)) = ?") < sql.index("SELECT TOP (?)")
    assert "LTRIM(RTRIM(V.COD_PARCEIRO)) = ?" in sql

    # No ignored-product marker when the caller explicitly requests test products.
    include_test = _request(
        product="20050012", partner_store="01", include_test_products=True,
    )
    test_sql, test_params = build_pending_export_sql(include_test, limit=12)
    assert test_sql.count("?") == len(test_params)
    assert test_params == ("01", "20050012", "001692", "01", 12)

    # Protect the older, non-CTE return export: TOP (?) is before its WHERE.
    legacy_sql, legacy_params = build_export_sql(request, limit=20)
    assert legacy_sql.index("SELECT TOP (?)") < legacy_sql.index("WHERE")
    assert legacy_params == (20, "01", "20050012", "001692", "01", "99999999")


def test_supplier_report_maps_totals_and_csv():
    repo = MagicMock()
    repo.get_pending_report_summary.return_value = {
        "supplier_count": 1,
        "product_count": 1,
        "shipment_count": 2,
        "pending_quantity": Decimal("4"),
        "unit_count": 1,
        "unit": "UN",
    }
    repo.list_pending_report_rows.return_value = [
        {
            "supplier_code": "001692",
            "supplier_store": "01",
            "supplier_name": "BELCABOS IND DE COND ELETRICOS LTDA",
            "product_code": "20050017",
            "product_description": "CARRETEL PLASTICO N 07",
            "unit": "UN",
            "shipment_count": 2,
            "received_quantity": Decimal("4"),
            "returned_quantity": Decimal("0"),
            "pending_quantity": Decimal("4"),
        }
    ]
    repo.list_pending_export_rows.return_value = repo.list_pending_report_rows.return_value
    use_case = PendingSupplierReportUseCase(repo)
    page = use_case.execute(_request())
    assert page["summary"]["supplier_count"] == 1
    assert page["summary"]["pending_quantity"] == 4
    assert page["items"][0]["shipment_count"] == 2
    assert page["items"][0]["supplier_name"].startswith("BELCABOS")
    assert page["total"] == 1
    exported = use_case.export(_request(export_format="csv"))
    assert exported["exported_count"] == 1
    text = exported["stream"].read().decode("utf-8-sig")
    assert "BELCABOS" in text
    assert "20050017" in text

    exported_xlsx = use_case.export(_request(export_format="xlsx"))
    assert exported_xlsx["exported_count"] == 1
    assert exported_xlsx["content_type"] == (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    worksheet = load_workbook(exported_xlsx["stream"], read_only=True, data_only=True).active
    rows = list(worksheet.values)
    assert rows[0][1] == "Fornecedor"
    assert rows[1][1] == "001692"
    assert rows[1][2] == "01"
    assert rows[1][3].startswith("BELCABOS")
    assert rows[1][4] == "20050017"
    assert rows[1][-1] == 4


def test_mixed_units_are_not_summed_in_kpi():
    repo = MagicMock()
    repo.get_pending_report_summary.return_value = {
        "supplier_count": 2,
        "product_count": 2,
        "shipment_count": 2,
        "pending_quantity": Decimal("12"),
        "unit_count": 2,
        "unit": "UN",
    }
    repo.list_pending_report_rows.return_value = []
    result = PendingSupplierReportUseCase(repo).execute(_request())
    assert result["summary"]["mixed_units"] is True
    assert result["summary"]["pending_quantity"] is None


def test_export_fails_closed_for_more_than_limit():
    repo = MagicMock()
    repo.get_pending_report_summary.return_value = {
        "supplier_count": 20001, "product_count": 20001, "shipment_count": 20001,
        "pending_quantity": 1, "unit_count": 1, "unit": "UN",
    }
    with pytest.raises(ValueError, match="excede o limite"):
        PendingSupplierReportUseCase(repo).export(_request())
    repo.list_pending_export_rows.assert_not_called()


def test_pending_report_router_contract_and_branch_access():
    from app.interface.http.routes.supplies.third_party_materials_router import router
    paths = {route.path for route in router.routes if hasattr(route, "path")}
    pending = next(route for route in router.routes if route.path.endswith("/pending-by-supplier"))
    pending_export = next(
        route for route in router.routes if route.path.endswith("/pending-by-supplier/export")
    )
    assert pending.operation_id == "get_supplies_third_party_materials_pending_suppliers"
    assert pending_export.operation_id == "export_supplies_third_party_materials_pending_suppliers"
    assert "/supplies/third-party-materials/pending-by-supplier" in paths
    assert "/supplies/third-party-materials/pending-by-supplier/export" in paths

    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)
    with patch(
        "app.interface.http.routes.supplies.third_party_materials_router.branch_access_error",
        return_value=None,
    ), patch(
        "app.interface.http.routes.supplies.third_party_materials_router.build_pending_supplier_report_use_case",
    ) as builder:
        builder.return_value.execute.return_value = {
            "items": [], "summary": {"supplier_count": 0}, "total": 0,
            "page": 1, "page_size": 20, "total_pages": 1,
        }
        response = client.get(
            "/supplies/third-party-materials/pending-by-supplier",
            params={"branch": "01", "partner_code": "001692"},
        )
        assert response.status_code == 200
        assert response.json()["meta"]["operationId"] == "get_supplies_third_party_materials_pending_suppliers"
        assert builder.call_count == 1


def test_supplier_pending_export_http_returns_attachment_in_both_formats():
    from app.interface.http.routes.supplies.third_party_materials_router import router

    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)
    with patch(
        "app.interface.http.routes.supplies.third_party_materials_router.branch_access_error",
        return_value=None,
    ), patch(
        "app.interface.http.routes.supplies.third_party_materials_router.build_pending_supplier_report_use_case",
    ) as builder:
        for fmt, media_type in (
            ("csv", "text/csv; charset=utf-8"),
            ("xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
        ):
            filename = f"pendencias-fornecedor.{fmt}"
            builder.return_value.export.return_value = {
                "stream": BytesIO(b"sample-data"),
                "content_type": media_type,
                "filename": filename,
                "exported_count": 1,
            }
            response = client.get(
                "/supplies/third-party-materials/pending-by-supplier/export",
                params={
                    "branch": "01", "product": "20050012",
                    "partner_code": "000006", "partner_store": "01",
                    "export_format": fmt,
                },
            )
            assert response.status_code == 200
            assert response.content == b"sample-data"
            assert filename in response.headers["content-disposition"]
            assert response.headers["x-exported-count"] == "1"
            request = builder.return_value.export.call_args.args[0]
            assert request.branch == "01"
            assert request.partner_code == "000006"
            assert request.partner_store == "01"
            assert request.product == "20050012"
            assert request.export_format == fmt
