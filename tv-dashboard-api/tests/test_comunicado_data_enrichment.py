from unittest.mock import MagicMock

from tv_app.application.services.comunicado_data_enrichment_service import (
    ComunicadoDataEnrichmentService,
    _extract_series,
    reset_comunicado_data_block_cache,
)
from tv_app.application.services.tv_data_route_catalog_service import TvDataRouteCatalogService


def test_enrich_data_source_block_resolves_full_payload():
    gateway = MagicMock()
    gateway.fetch_by_operation_id.return_value = {
        "meta": {"operationId": "get_overall_equipment_effectiveness_pct", "shape": "playbook_report"},
        "data": {
            "summary": {"value": 78.4},
            "points": [{"label": "Jan", "value": 70}, {"label": "Fev", "value": 78.4}],
            "items": [{"produto": "A", "qty": 10}],
        },
        "route": {
            "label": "OEE",
            "valueFields": ["value"],
            "seriesField": "points",
            "tableFields": "items",
            "tvConstraints": {},
        },
    }
    service = ComunicadoDataEnrichmentService(
        catalog=TvDataRouteCatalogService(),
        gateway=gateway,
    )
    blocks = [
        {
            "id": "src-1",
            "type": "data_source",
            "dataBinding": {
                "operationId": "get_overall_equipment_effectiveness_pct",
                "params": {"periodDays": 7},
                "displayMode": "auto",
            },
        },
        {
            "id": "chart-1",
            "type": "chart_view",
            "dataSourceId": "src-1",
            "chartType": "line",
        },
    ]
    enriched = service.enrich_blocks(blocks, cfg={}, authorization="Bearer x")
    assert enriched[0]["resolved"]["kpi"]["value"] == 78.4
    assert enriched[0]["resolved"]["chart"]["points"]
    assert enriched[1]["resolved"]["kpi"]["value"] == 78.4


def test_enrich_data_kpi_block_resolves_scalar():
    gateway = MagicMock()
    gateway.fetch_by_operation_id.return_value = {
        "meta": {"operationId": "get_overall_equipment_effectiveness_pct", "shape": "scalar"},
        "data": {"summary": {"value": 78.4}},
        "route": {
            "label": "OEE",
            "valueFields": ["value", "oeePct"],
            "tvConstraints": {},
        },
    }
    service = ComunicadoDataEnrichmentService(
        catalog=TvDataRouteCatalogService(),
        gateway=gateway,
    )
    blocks = [
        {
            "id": "kpi-1",
            "type": "data_kpi",
            "frame": {"x": 5, "y": 5, "w": 30, "h": 20},
            "dataBinding": {
                "operationId": "get_overall_equipment_effectiveness_pct",
                "params": {"periodDays": 7},
                "displayMode": "kpi",
            },
        }
    ]
    cfg = {"dataFilters": {"branch": "01"}}
    enriched = service.enrich_blocks(blocks, cfg=cfg, authorization="Bearer x")
    assert enriched[0]["resolved"]["kpi"]["value"] == 78.4
    gateway.fetch_by_operation_id.assert_called_once()
    call_kwargs = gateway.fetch_by_operation_id.call_args.kwargs
    assert call_kwargs["params"]["branch"] == "01"
    assert call_kwargs["params"]["periodDays"] == 7


def test_enrich_rejects_disallowed_route():
    service = ComunicadoDataEnrichmentService(catalog=TvDataRouteCatalogService(), gateway=MagicMock())
    blocks = [
        {
            "id": "x",
            "type": "data_kpi",
            "dataBinding": {"operationId": "not_in_allowlist", "params": {}},
        }
    ]
    enriched = service.enrich_blocks(blocks, cfg={})
    assert "error" in enriched[0]["resolved"]


def test_fetch_cached_reuses_ttl_cache():
    reset_comunicado_data_block_cache()
    gateway = MagicMock()
    gateway.fetch_by_operation_id.return_value = {
        "meta": {"operationId": "get_overall_equipment_effectiveness_pct"},
        "data": {"summary": {"value": 1}},
        "route": {"valueFields": ["value"], "tvConstraints": {}},
    }
    service = ComunicadoDataEnrichmentService(
        catalog=TvDataRouteCatalogService(),
        gateway=gateway,
    )
    params = {"branch": "01", "periodDays": 7}
    service._fetch_cached("get_overall_equipment_effectiveness_pct", params, "Bearer x")
    service._fetch_cached("get_overall_equipment_effectiveness_pct", params, "Bearer x")
    assert gateway.fetch_by_operation_id.call_count == 1


def test_extract_series_periodo_and_branch_specific_field():
    payload = {
        "points": [
            {"periodo": "2026-07-01", "oee_filial_01": 72.1},
            {"periodo": "2026-07-02", "oee_filial_01": 74.5},
        ]
    }
    points = _extract_series(payload, "points", branch="01")
    assert len(points) == 2
    assert points[0]["label"] == "2026-07-01"
    assert points[0]["value"] == 72.1
    assert points[1]["value"] == 74.5


def test_extract_series_otd_branch_fallback():
    payload = {
        "points": [
            {"periodo": "2026-07-01", "otd_filial_02": 88.0},
        ]
    }
    points = _extract_series(payload, "points", branch="2")
    assert points[0]["value"] == 88.0


def test_enrich_rejects_branch_outside_static_policy(monkeypatch):
    monkeypatch.setattr(
        "tv_app.application.services.branch_policy_service.allowed_branches",
        lambda: ["01", "02"],
    )
    gateway = MagicMock()
    service = ComunicadoDataEnrichmentService(
        catalog=TvDataRouteCatalogService(),
        gateway=gateway,
    )
    blocks = [
        {
            "id": "kpi-1",
            "type": "data_kpi",
            "dataBinding": {
                "operationId": "get_overall_equipment_effectiveness_pct",
                "params": {},
            },
        }
    ]
    enriched = service.enrich_blocks(blocks, cfg={"dataFilters": {"branch": "99"}}, authorization="Bearer x")
    assert enriched[0]["resolved"]["error"]
    gateway.fetch_by_operation_id.assert_not_called()


def test_enrich_rejects_branch_for_scoped_user():
    gateway = MagicMock()
    user = MagicMock()
    user.is_superadmin = False
    user.permissions = ["tv-dashboard.view.filial-01"]
    service = ComunicadoDataEnrichmentService(
        catalog=TvDataRouteCatalogService(),
        gateway=gateway,
    )
    blocks = [
        {
            "id": "kpi-1",
            "type": "data_kpi",
            "dataBinding": {
                "operationId": "get_overall_equipment_effectiveness_pct",
                "params": {"branch": "02"},
            },
        }
    ]
    enriched = service.enrich_blocks(blocks, cfg={}, authorization="Bearer x", user=user)
    assert enriched[0]["resolved"]["error"]
    gateway.fetch_by_operation_id.assert_not_called()


def test_enrich_data_metric_auto_resolves_table_for_paged_list():
    gateway = MagicMock()
    gateway.fetch_by_operation_id.return_value = {
        "meta": {"operationId": "search_products", "shape": "paged_list"},
        "data": {
            "items": [
                {"code": "90123456", "name": "Produto A", "value": 1200.5},
            ]
        },
        "route": {
            "label": "Produtos",
            "tableFields": "items",
            "metaShape": "paged_list",
            "tvConstraints": {"maxRows": 5},
        },
    }
    service = ComunicadoDataEnrichmentService(
        catalog=TvDataRouteCatalogService(),
        gateway=gateway,
    )
    blocks = [
        {
            "id": "tbl-1",
            "type": "data_metric",
            "dataBinding": {
                "operationId": "search_products",
                "params": {"limit": 5},
                "displayMode": "auto",
            },
        }
    ]
    enriched = service.enrich_blocks(blocks, cfg={}, authorization="Bearer x")
    rows = enriched[0]["resolved"]["table"]["rows"]
    assert rows[0]["code"] == "90123456"
    assert rows[0]["name"] == "Produto A"
    columns = enriched[0]["resolved"]["table"]["columns"]
    assert any(column["key"] == "code" for column in columns)


def test_enrich_scalar_route_as_line_chart():
    gateway = MagicMock()
    gateway.fetch_by_operation_id.return_value = {
        "meta": {"operationId": "get_overall_equipment_effectiveness_pct", "shape": "scalar"},
        "data": {"summary": {"value": 78.4}},
        "route": {
            "label": "OEE",
            "valueFields": ["value"],
            "tvConstraints": {},
        },
    }
    service = ComunicadoDataEnrichmentService(
        catalog=TvDataRouteCatalogService(),
        gateway=gateway,
    )
    blocks = [
        {
            "id": "chart-1",
            "type": "data_chart",
            "dataBinding": {
                "operationId": "get_overall_equipment_effectiveness_pct",
                "displayMode": "line_chart",
            },
        }
    ]
    enriched = service.enrich_blocks(blocks, cfg={}, authorization="Bearer x")
    points = enriched[0]["resolved"]["chart"]["points"]
    assert len(points) == 1
    assert points[0]["value"] == 78.4


def test_enrich_series_route_as_kpi_uses_last_point():
    gateway = MagicMock()
    gateway.fetch_by_operation_id.return_value = {
        "meta": {"operationId": "get_production_oee_series", "shape": "playbook_report"},
        "data": {
            "points": [
                {"periodo": "2026-07-01", "value": 70.0},
                {"periodo": "2026-07-02", "value": 75.5},
            ]
        },
        "route": {
            "label": "OEE série",
            "seriesField": "points",
            "valueFields": ["value"],
            "tvConstraints": {},
        },
    }
    service = ComunicadoDataEnrichmentService(
        catalog=TvDataRouteCatalogService(),
        gateway=gateway,
    )
    blocks = [
        {
            "id": "kpi-1",
            "type": "data_kpi",
            "dataBinding": {
                "operationId": "get_production_oee_series",
                "displayMode": "kpi",
            },
        }
    ]
    enriched = service.enrich_blocks(blocks, cfg={}, authorization="Bearer x")
    assert enriched[0]["resolved"]["kpi"]["value"] == 75.5


def test_enrich_data_source_resolves_series_as_table_rows():
    gateway = MagicMock()
    gateway.fetch_by_operation_id.return_value = {
        "meta": {"operationId": "get_production_otd_series", "shape": "scalar"},
        "data": {
            "points": [
                {"periodo": "2026-07-01", "otd_filial_01": 88.0, "otd_filial_02": 72.0},
                {"periodo": "2026-07-02", "otd_filial_01": 90.5, "otd_filial_02": 74.0},
            ]
        },
        "route": {
            "label": "OTD — série temporal",
            "seriesField": "points",
            "tvConstraints": {},
        },
    }
    service = ComunicadoDataEnrichmentService(
        catalog=TvDataRouteCatalogService(),
        gateway=gateway,
    )
    blocks = [
        {
            "id": "src-1",
            "type": "data_source",
            "dataBinding": {
                "operationId": "get_production_otd_series",
                "params": {"branch": "01", "periodDays": 30},
                "displayMode": "auto",
            },
        },
        {
            "id": "tbl-1",
            "type": "table_view",
            "dataSourceId": "src-1",
            "tablePreset": "standard",
            "maxRows": 3,
        },
    ]
    enriched = service.enrich_blocks(blocks, cfg={}, authorization="Bearer x")
    table_rows = enriched[0]["resolved"]["table"]["rows"]
    assert len(table_rows) == 2
    assert table_rows[0]["periodo"] == "2026-07-01"
    assert table_rows[0]["value"] == 88.0
    assert enriched[1]["resolved"]["table"]["rows"][0]["value"] == 88.0


def test_enrich_honors_value_field_override():
    reset_comunicado_data_block_cache()
    gateway = MagicMock()
    gateway.fetch_by_operation_id.return_value = {
        "meta": {"operationId": "get_overall_equipment_effectiveness_pct", "shape": "scalar"},
        "data": {"summary": {"value": 10, "oeePct": 88.2}},
        "route": {
            "valueFields": ["value", "oeePct"],
            "tvConstraints": {},
        },
    }
    service = ComunicadoDataEnrichmentService(
        catalog=TvDataRouteCatalogService(),
        gateway=gateway,
    )
    blocks = [
        {
            "id": "kpi-1",
            "type": "data_kpi",
            "dataBinding": {
                "operationId": "get_overall_equipment_effectiveness_pct",
                "displayMode": "kpi",
                "valueField": "oeePct",
            },
        }
    ]
    enriched = service.enrich_blocks(blocks, cfg={}, authorization="Bearer x")
    assert enriched[0]["resolved"]["kpi"]["value"] == 88.2
