"""Smoke: rotas amostra por módulo retornam meta semântico no envelope."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.application.services.response_meta_builder import DATA_VERSION


def _assert_meta(body: dict, *, operation_id: str, shape: str) -> None:
    assert body.get("success") is True
    meta = body.get("meta")
    assert isinstance(meta, dict), body
    assert meta.get("operationId") == operation_id
    assert meta.get("shape") == shape
    assert meta.get("dataVersion") == DATA_VERSION
    assert isinstance(meta.get("entity"), str) and meta["entity"]


def _body(response) -> dict:
    return json.loads(response.body.decode())


@patch(
    "app.interface.http.routes.supplies.supplies_router.enrich_dashboard_metric",
    side_effect=lambda payload, **_: payload,
)
@patch("app.interface.http.routes.supplies.supplies_router.build_get_cpv_use_case")
def test_supplies_cpv_returns_meta(mock_build, _mock_enrich) -> None:
    from app.interface.http.routes.supplies.supplies_router import get_cpv

    mock_use_case = MagicMock()
    mock_use_case.execute.return_value = {"summary": {"value": 1}}
    mock_build.return_value = mock_use_case

    response = get_cpv()
    _assert_meta(
        _body(response),
        operation_id="get_supplies_cpv",
        shape="scalar",
    )


@patch(
    "app.interface.http.routes.commercial.commercial_router.enrich_dashboard_metric",
    side_effect=lambda payload, **_: payload,
)
@patch(
    "app.interface.http.routes.commercial.commercial_router.build_get_sales_conversion_rate_use_case"
)
def test_commercial_closing_rate_returns_meta(mock_build, _mock_enrich) -> None:
    from app.interface.http.routes.commercial.commercial_router import (
        get_sales_conversion_rate,
    )

    mock_use_case = MagicMock()
    mock_use_case.execute.return_value = {"rate_pct": 12.5}
    mock_build.return_value = mock_use_case

    response = get_sales_conversion_rate()
    _assert_meta(
        _body(response),
        operation_id="get_sales_conversion_rate",
        shape="scalar",
    )


@patch("app.interface.http.routes.engineering.engineering_router.build_engineering_list_lmps_use_case")
def test_engineering_list_lmps_returns_meta(mock_build) -> None:
    from app.interface.http.routes.engineering.engineering_router import list_lmps_route

    mock_result = MagicMock()
    mock_result.to_dict.return_value = {
        "items": [],
        "page": 1,
        "page_size": 50,
        "total": 0,
    }
    mock_use_case = MagicMock()
    mock_use_case.execute.return_value = mock_result
    mock_build.return_value = mock_use_case

    response = list_lmps_route()
    _assert_meta(
        _body(response),
        operation_id="list_lmps",
        shape="paged_list",
    )


@patch(
    "app.interface.http.routes.quality.quality_router.enrich_dashboard_metric",
    side_effect=lambda payload, **_: payload,
)
@patch("app.interface.http.routes.quality.quality_router.build_get_kaizen_summary_use_case")
def test_quality_kaizen_summary_returns_meta(mock_build, _mock_enrich) -> None:
    from app.interface.http.routes.quality.quality_router import get_kaizen_summary

    mock_summary = MagicMock()
    mock_summary.to_dict.return_value = {"total": 3}
    mock_use_case = MagicMock()
    mock_use_case.execute.return_value = mock_summary
    mock_build.return_value = mock_use_case

    response = get_kaizen_summary()
    _assert_meta(
        _body(response),
        operation_id="get_kaizen_summary",
        shape="scalar",
    )


@patch("app.interface.http.routes.quality.quality_router.build_get_kaizen_by_id_use_case")
def test_quality_kaizen_by_id_returns_meta(mock_build) -> None:
    from app.domain.entities.kaizen.kaizen import KaizenDetail
    from app.interface.http.routes.quality.quality_router import get_kaizen_by_id

    mock_build.return_value.execute.return_value = KaizenDetail(
        id="01-16/01/2026-App resina CT-16",
        title="App resina CT-16",
        date_implemented="16/01/2026",
        status="implantado",
        accountable="Ossamu",
        sector="Producao",
        investment=620.0,
        daily_savings=7.54,
        annual_savings=2752.10,
        branch="01",
    )

    response = get_kaizen_by_id("01-16/01/2026-App resina CT-16")
    _assert_meta(
        _body(response),
        operation_id="get_kaizen_by_id",
        shape="scalar",
    )


@patch("app.interface.http.routes.quality.kaizen_records_router.build_kaizen_repository")
def test_quality_kaizen_records_list_returns_meta(mock_build) -> None:
    from app.interface.http.routes.quality.kaizen_records_router import list_kaizen_records

    mock_repo = MagicMock()
    mock_repo.list_records.return_value = {
        "items": [],
        "pagination": {"page": 1, "page_size": 50, "total": 0, "total_pages": 1},
    }
    mock_build.return_value = mock_repo

    response = list_kaizen_records()
    _assert_meta(
        _body(response),
        operation_id="list_kaizen_records",
        shape="paged_list",
    )


@patch("app.interface.http.routes.quality.kaizen_records_router.build_kaizen_repository")
def test_quality_kaizen_records_create_returns_meta(mock_build) -> None:
    from app.interface.http.routes.quality.kaizen_records_router import (
        KaizenRecordBody,
        create_kaizen_record,
    )

    mock_repo = MagicMock()
    mock_repo.create_record.return_value = {
        "id": "11111111-1111-4111-8111-111111111111",
        "branch_code": "01",
        "title": "Kaizen teste",
        "savings_type": "qualitativo",
        "status": "recebido",
    }
    mock_build.return_value = mock_repo

    response = create_kaizen_record(
        body=KaizenRecordBody(branch_code="01", title="Kaizen teste"),
    )
    _assert_meta(
        _body(response),
        operation_id="create_kaizen_record",
        shape="scalar",
    )


@patch("app.interface.http.routes.quality.kaizen_records_router.build_kaizen_repository")
def test_quality_kaizen_export_returns_meta(mock_build) -> None:
    from app.interface.http.routes.quality.kaizen_records_router import export_kaizen_records

    mock_repo = MagicMock()
    mock_repo.export_records.return_value = [{"branch_code": "01", "title": "Kaizen teste"}]
    mock_build.return_value = mock_repo

    response = export_kaizen_records()
    _assert_meta(
        _body(response),
        operation_id="export_kaizen_records",
        shape="scalar",
    )


@patch("app.interface.http.routes.quality.kaizen_records_router.build_kaizen_repository")
def test_quality_kaizen_records_summary_returns_meta(mock_build) -> None:
    from app.interface.http.routes.quality.kaizen_records_router import (
        get_kaizen_records_summary,
    )

    mock_repo = MagicMock()
    mock_repo.summary.return_value = {
        "total": 0,
        "period_savings": 0.0,
        "period_implanted_count": 0,
        "implanted_by_month": [],
        "by_status": [],
        "recent": [],
    }
    mock_build.return_value = mock_repo

    response = get_kaizen_records_summary()
    _assert_meta(
        _body(response),
        operation_id="get_kaizen_records_summary",
        shape="scalar",
    )


@patch("app.interface.http.routes.quality.kaizen_records_router.build_import_kaizens_use_case")
def test_quality_kaizen_import_returns_meta(mock_build) -> None:
    from app.application.use_cases.kaizen.import_kaizens_use_case import ImportKaizensResult
    from app.interface.http.routes.quality.kaizen_records_router import (
        ImportKaizensBody,
        import_kaizen_records,
    )

    mock_build.return_value.execute.return_value = ImportKaizensResult(
        created=1,
        skipped=0,
        errors=0,
        items=[],
    )

    response = import_kaizen_records(
        body=ImportKaizensBody(items=[{"branch_code": "01", "title": "Kaizen teste"}]),
    )
    _assert_meta(
        _body(response),
        operation_id="import_kaizen_records",
        shape="scalar",
    )


@patch("app.interface.http.routes.quality.ppm_routes.build_get_produced_quantity_use_case")
def test_quality_produced_quantity_returns_meta(mock_build) -> None:
    from app.interface.http.routes.quality.ppm_routes import get_produced_quantity

    mock_report = MagicMock()
    mock_report.to_dict.return_value = {
        "branch": "01",
        "date_start": "2026-01-01",
        "date_end": "2026-01-31",
        "products": ["50232465"],
        "items": [],
        "total_produced_milheiro": 0.0,
        "total_produced_un": 0.0,
        "by_product": [],
    }
    mock_use_case = MagicMock()
    mock_use_case.execute.return_value = mock_report
    mock_build.return_value = mock_use_case

    response = get_produced_quantity(
        product=["50232465"],
        branch="01",
        date_start="2026-01-01",
        date_end="2026-01-31",
    )
    _assert_meta(
        _body(response),
        operation_id="get_produced_quantity",
        shape="playbook_report",
    )


@patch("app.interface.http.routes.hr.hr_router.build_hr_metrics_repository")
def test_hr_branches_returns_meta(mock_build) -> None:
    from app.interface.http.routes.hr.hr_router import list_hr_branches

    mock_repo = MagicMock()
    mock_repo.list_active_branches.return_value = ["01", "02"]
    mock_build.return_value = mock_repo

    response = list_hr_branches()
    _assert_meta(
        _body(response),
        operation_id="list_hr_branches",
        shape="scalar",
    )


@patch("app.interface.http.routes.quality.quality_router.build_list_quality_branches_use_case")
def test_quality_branches_returns_meta(mock_build) -> None:
    from app.application.dto.quality.quality_branches_response import (
        QualityBranchesResponse,
    )
    from app.interface.http.routes.quality.quality_router import list_quality_branches

    mock_use_case = MagicMock()
    mock_use_case.execute.return_value = QualityBranchesResponse(branches=["01", "02"])
    mock_build.return_value = mock_use_case

    response = list_quality_branches(
        date_start="2026-06-01",
        date_end="2026-06-09",
    )
    body = _body(response)
    assert body.get("success") is True
    assert body.get("data", {}).get("branches") == ["01", "02"]
    _assert_meta(
        body,
        operation_id="list_quality_branches",
        shape="scalar",
    )


@patch("app.interface.http.routes.system_routes.build_search_tables_by_description_use_case")
def test_system_search_tables_returns_meta(mock_build) -> None:
    from app.interface.http.routes.system_routes import search_tables

    mock_use_case = MagicMock()
    mock_use_case.execute.return_value = {
        "items": [],
        "page": 1,
        "page_size": 20,
        "total": 0,
    }
    mock_build.return_value = mock_use_case

    response = search_tables(description="produto", page=1, limit=20)
    _assert_meta(
        _body(response),
        operation_id="search_tables_by_description",
        shape="paged_list",
    )


@patch("app.interface.http.routes.sale_routes.build_list_sale_order_use_case")
def test_sale_orders_list_returns_meta(mock_build) -> None:
    from app.interface.http.routes.sale_routes import list_sale_order_route

    mock_result = MagicMock()
    mock_result.to_dict.return_value = {
        "items": [],
        "page": 1,
        "page_size": 50,
        "total": 0,
    }
    mock_use_case = MagicMock()
    mock_use_case.execute.return_value = mock_result
    mock_build.return_value = mock_use_case

    response = list_sale_order_route()
    _assert_meta(
        _body(response),
        operation_id="list_sale_orders",
        shape="paged_list",
    )


@patch(
    "app.interface.http.routes.production.production_router.enrich_dashboard_metric",
    side_effect=lambda payload, **_: payload,
)
@patch(
    "app.interface.http.routes.production.production_router.build_get_on_time_delivery_pct_use_case"
)
def test_production_otd_returns_meta(mock_build, _mock_enrich) -> None:
    from app.interface.http.routes.production.production_router import (
        get_on_time_delivery_pct,
    )

    mock_use_case = MagicMock()
    mock_use_case.execute.return_value = {"otd_pct": 88.0}
    mock_build.return_value = mock_use_case

    response = get_on_time_delivery_pct()
    _assert_meta(
        _body(response),
        operation_id="get_on_time_delivery_pct",
        shape="scalar",
    )


@patch(
    "app.interface.http.routes.scheduling.scheduling_router._branch_view_allowed",
    return_value=True,
)
@patch("app.interface.http.routes.scheduling.scheduling_router.build_scheduling_repository")
def test_scheduling_resources_returns_meta(mock_build, _mock_branch) -> None:
    from app.interface.http.routes.scheduling.scheduling_router import list_resources

    mock_repo = MagicMock()
    mock_repo.list_resources.return_value = []
    mock_build.return_value = mock_repo

    response = list_resources(branch="ES", active=True)
    _assert_meta(
        _body(response),
        operation_id="list_scheduling_resources",
        shape="paged_list",
    )


@pytest.mark.asyncio
@patch("app.interface.http.routes.data_routes.build_run_sql_use_case")
async def test_data_sql_returns_meta(mock_build) -> None:
    from app.interface.http.routes.data_routes import execute_sql_raw

    mock_use_case = MagicMock()
    mock_use_case.execute.return_value = {
        "items": [],
        "page": 1,
        "page_size": 50,
        "total": 0,
    }
    mock_build.return_value = mock_use_case

    request = MagicMock()
    request.headers.get.return_value = "application/json"
    request.json = AsyncMock(return_value={"sql": "SELECT 1"})

    response = await execute_sql_raw(request)
    _assert_meta(
        _body(response),
        operation_id="execute_readonly_sql",
        shape="paged_list",
    )

@patch(
    "app.interface.http.routes.pedidos_venda_abertos.pedidos_venda_abertos_router.build_list_pedidos_venda_abertos_use_case"
)
def test_pedidos_venda_abertos_returns_meta(mock_build) -> None:
    from app.interface.http.routes.pedidos_venda_abertos.pedidos_venda_abertos_router import (
        list_pedidos_venda_abertos_route,
    )

    mock_result = MagicMock()
    mock_result.to_dict.return_value = {
        "items": [],
        "summary": {"total_linhas": 0},
    }
    mock_use_case = MagicMock()
    mock_use_case.execute.return_value = mock_result
    mock_build.return_value = mock_use_case

    response = list_pedidos_venda_abertos_route()
    _assert_meta(
        _body(response),
        operation_id="list_pedidos_venda_abertos",
        shape="composite_analysis",
    )


@patch(
    "app.interface.http.routes.pedidos_venda_abertos.pedidos_venda_abertos_router.build_list_ops_abertas_use_case"
)
def test_ops_abertas_pedidos_venda_returns_meta(mock_build) -> None:
    from app.interface.http.routes.pedidos_venda_abertos.pedidos_venda_abertos_router import (
        list_ops_abertas_route,
    )

    mock_result = MagicMock()
    mock_result.to_dict.return_value = {
        "items": [],
        "resumo": [],
    }
    mock_use_case = MagicMock()
    mock_use_case.execute.return_value = mock_result
    mock_build.return_value = mock_use_case

    response = list_ops_abertas_route()
    _assert_meta(
        _body(response),
        operation_id="list_ops_abertas_pedidos_venda",
        shape="composite_analysis",
    )


@patch(
    "app.interface.http.routes.inspecoes_entrada.inspecoes_entrada_router._branch_view_allowed",
    return_value=True,
)
@patch(
    "app.interface.http.routes.inspecoes_entrada.inspecoes_entrada_router.build_get_inspecoes_entrada_resumo_use_case"
)
def test_inspecoes_entrada_resumo_returns_meta(mock_build, _mock_branch) -> None:
    from app.interface.http.routes.inspecoes_entrada.inspecoes_entrada_router import (
        get_inspecoes_entrada_resumo_route,
    )

    mock_result = MagicMock()
    mock_result.to_dict.return_value = {
        "branch": "01",
        "pending_inspections": 6,
        "inspected": 731,
        "approved_inspections": 730,
        "rejected_inspections": 1,
        "approval_rate": 99.86,
        "inspections_with_time": 728,
        "average_time_hours": 16.46,
        "average_time_days": 0.69,
    }
    mock_use_case = MagicMock()
    mock_use_case.execute.return_value = mock_result
    mock_build.return_value = mock_use_case

    response = get_inspecoes_entrada_resumo_route(branch="01")
    _assert_meta(
        _body(response),
        operation_id="get_inspecoes_entrada_resumo",
        shape="scalar",
    )


@patch(
    "app.interface.http.routes.inspecoes_entrada.inspecoes_entrada_router._branch_view_allowed",
    return_value=True,
)
@patch(
    "app.interface.http.routes.inspecoes_entrada.inspecoes_entrada_router.build_list_inspecoes_entrada_pendentes_use_case"
)
def test_inspecoes_entrada_pendentes_returns_meta(mock_build, _mock_branch) -> None:
    from app.interface.http.routes.inspecoes_entrada.inspecoes_entrada_router import (
        get_inspecoes_entrada_pendentes_route,
    )

    mock_result = MagicMock()
    mock_result.to_dict.return_value = {
        "branch": "01",
        "items": [],
        "pagination": {"page": 1, "page_size": 50, "total": 0, "total_pages": 1},
    }
    mock_use_case = MagicMock()
    mock_use_case.execute.return_value = mock_result
    mock_build.return_value = mock_use_case

    response = get_inspecoes_entrada_pendentes_route(branch="01", page=1, page_size=50)
    _assert_meta(
        _body(response),
        operation_id="get_inspecoes_entrada_pendentes",
        shape="paged_list",
    )


@patch(
    "app.interface.http.routes.inspecoes_entrada.inspecoes_entrada_router._branch_view_allowed",
    return_value=True,
)
@patch(
    "app.interface.http.routes.inspecoes_entrada.inspecoes_entrada_router.build_list_inspecoes_entrada_pendentes_fornecedor_use_case"
)
def test_inspecoes_entrada_pendentes_fornecedor_returns_meta(
    mock_build,
    _mock_branch,
) -> None:
    from app.interface.http.routes.inspecoes_entrada.inspecoes_entrada_router import (
        get_inspecoes_entrada_pendentes_fornecedor_route,
    )

    mock_result = MagicMock()
    mock_result.to_dict.return_value = {
        "branch": "01",
        "items": [],
        "total_suppliers": 0,
        "total_pending": 0,
    }
    mock_use_case = MagicMock()
    mock_use_case.execute.return_value = mock_result
    mock_build.return_value = mock_use_case

    response = get_inspecoes_entrada_pendentes_fornecedor_route(branch="01")
    _assert_meta(
        _body(response),
        operation_id="get_inspecoes_entrada_pendentes_fornecedor",
        shape="list",
    )


@patch(
    "app.interface.http.routes.inspecoes_entrada.inspecoes_entrada_router._branch_view_allowed",
    return_value=True,
)
@patch(
    "app.interface.http.routes.inspecoes_entrada.inspecoes_entrada_router.build_list_inspecoes_entrada_rejeitadas_ensaiador_use_case"
)
def test_inspecoes_entrada_rejeitadas_ensaiador_returns_meta(
    mock_build,
    _mock_branch,
) -> None:
    from app.interface.http.routes.inspecoes_entrada.inspecoes_entrada_router import (
        get_inspecoes_entrada_rejeitadas_ensaiador_route,
    )

    mock_result = MagicMock()
    mock_result.to_dict.return_value = {
        "branch": "01",
        "items": [],
        "total_inspectors": 0,
        "total_rejected": 0,
    }
    mock_use_case = MagicMock()
    mock_use_case.execute.return_value = mock_result
    mock_build.return_value = mock_use_case

    response = get_inspecoes_entrada_rejeitadas_ensaiador_route(branch="01")
    _assert_meta(
        _body(response),
        operation_id="get_inspecoes_entrada_rejeitadas_ensaiador",
        shape="list",
    )


@patch(
    "app.interface.http.routes.inspecoes_entrada.inspecoes_entrada_router._branch_view_allowed",
    return_value=True,
)
@patch(
    "app.interface.http.routes.inspecoes_entrada.inspecoes_entrada_router.build_list_inspecoes_entrada_historico_use_case"
)
def test_inspecoes_entrada_historico_returns_meta(mock_build, _mock_branch) -> None:
    from app.interface.http.routes.inspecoes_entrada.inspecoes_entrada_router import (
        get_inspecoes_entrada_historico_route,
    )

    mock_result = MagicMock()
    mock_result.to_dict.return_value = {
        "branch": "01",
        "items": [],
        "pagination": {
            "page": 1,
            "page_size": 50,
            "total": 731,
            "total_pages": 15,
        },
        "filters": {
            "result": None,
            "date_from": None,
            "date_to": None,
            "supplier": None,
            "product_code": None,
            "inspector": None,
            "invoice_number": None,
            "lot": None,
        },
    }
    mock_use_case = MagicMock()
    mock_use_case.execute.return_value = mock_result
    mock_build.return_value = mock_use_case

    response = get_inspecoes_entrada_historico_route(
        branch="01",
        page=1,
        page_size=50,
        result=None,
        date_from=None,
        date_to=None,
        supplier=None,
        product_code=None,
        inspector=None,
        invoice_number=None,
        lot=None,
    )
    _assert_meta(
        _body(response),
        operation_id="get_inspecoes_entrada_historico",
        shape="paged_list",
    )


@patch(
    "app.interface.http.routes.inspecoes_entrada.inspecoes_entrada_router._branch_view_allowed",
    return_value=True,
)
@patch(
    "app.interface.http.routes.inspecoes_entrada.inspecoes_entrada_router.build_get_inspecoes_entrada_historico_detalhe_use_case"
)
def test_inspecoes_entrada_historico_detalhe_meta(mock_build, _mock_branch) -> None:
    from app.interface.http.routes.inspecoes_entrada.inspecoes_entrada_router import (
        get_inspecoes_entrada_historico_detalhe_route,
    )

    mock_result = MagicMock()
    mock_result.to_dict.return_value = {
        "branch": "01",
        "inspection_id": "01|000042999|2|0002|000532|01|10110388|AUTO000952",
        "summary": {},
        "tests": [],
        "totals": {
            "tests_count": 0,
            "approved_tests_count": 0,
            "failed_tests_count": 0,
        },
    }
    mock_use_case = MagicMock()
    mock_use_case.execute.return_value = mock_result
    mock_build.return_value = mock_use_case

    response = get_inspecoes_entrada_historico_detalhe_route(
        branch="01",
        inspection_id="01|000042999|2|0002|000532|01|10110388|AUTO000952",
    )
    _assert_meta(
        _body(response),
        operation_id="get_inspecoes_entrada_historico_detalhe",
        shape="object",
    )

