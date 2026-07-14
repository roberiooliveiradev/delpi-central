from unittest.mock import MagicMock

from tv_app.application.services.comunicado_data_enrichment_service import (
    ComunicadoDataEnrichmentService,
    _extract_scalar_value,
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


def test_enrich_blocks_dedupes_identical_sources_in_one_request():
    """Duas fontes iguais no mesmo assemble ⇒ um único fetch_by_operation_id."""
    reset_comunicado_data_block_cache()
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
    binding = {
        "operationId": "get_overall_equipment_effectiveness_pct",
        "params": {"periodDays": 7},
        "displayMode": "kpi",
    }
    blocks = [
        {"id": "kpi-a", "type": "data_kpi", "dataBinding": dict(binding)},
        {"id": "kpi-b", "type": "data_kpi", "dataBinding": dict(binding)},
    ]
    enriched = service.enrich_blocks(blocks, cfg={}, authorization="Bearer x")
    assert gateway.fetch_by_operation_id.call_count == 1
    assert enriched[0]["resolved"]["kpi"]["value"] == 78.4
    assert enriched[1]["resolved"]["kpi"]["value"] == 78.4


def test_fetch_cached_force_refresh_bypasses_ttl():
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
    service._fetch_cached(
        "get_overall_equipment_effectiveness_pct",
        params,
        "Bearer x",
        force_refresh=True,
    )
    assert gateway.fetch_by_operation_id.call_count == 2


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


def test_enrich_data_source_series_table_keeps_full_series_without_max_rows():
    """Tabela alinhada ao gráfico: sem maxRows explícito, não truncar a série em 5."""
    points = [
        {"periodo": f"2026-06-{day:02d}", "value": 70.0 + day}
        for day in range(1, 13)
    ]
    gateway = MagicMock()
    gateway.fetch_by_operation_id.return_value = {
        "meta": {"operationId": "get_production_oee_series", "shape": "playbook_report"},
        "data": {"points": points},
        "route": {
            "label": "OEE — série temporal",
            "seriesField": "points",
            "tvConstraints": {"requiresBranchPermission": True},
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
                "operationId": "get_production_oee_series",
                "params": {"periodDays": 30},
                "displayMode": "auto",
            },
        }
    ]
    enriched = service.enrich_blocks(blocks, cfg={}, authorization="Bearer x")
    resolved = enriched[0]["resolved"]
    assert len(resolved["chart"]["points"]) == 12
    assert len(resolved["table"]["rows"]) == 12


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


def test_extract_scalar_value_fallback_pct_without_value_fields():
    data = {"sales_conversion_rate_pct": 13.9, "qtd_proposals": 41, "qtd_won": 5}
    assert _extract_scalar_value(data, []) == 13.9
    assert _extract_scalar_value(data, ["sales_conversion_rate_pct"]) == 13.9


def test_enrich_sales_conversion_rate_resolves_kpi_and_chart_point():
    gateway = MagicMock()
    gateway.fetch_by_operation_id.return_value = {
        "meta": {"operationId": "get_sales_conversion_rate", "shape": "scalar"},
        "data": {"sales_conversion_rate_pct": 13.9, "qtd_proposals": 41, "qtd_won": 5},
        "route": {
            "label": "Taxa de fechamento",
            "valueFields": ["sales_conversion_rate_pct", "value"],
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
                "operationId": "get_sales_conversion_rate",
                "params": {"periodDays": 30},
                "displayMode": "kpi",
            },
        },
        {
            "id": "kpi-1",
            "type": "kpi_view",
            "dataSourceId": "src-1",
        },
        {
            "id": "chart-1",
            "type": "chart_view",
            "dataSourceId": "src-1",
            "chartType": "line",
        },
    ]
    enriched = service.enrich_blocks(blocks, cfg={}, authorization="Bearer x")
    assert enriched[0]["resolved"]["kpi"]["value"] == 13.9
    assert enriched[0]["resolved"]["chart"]["points"]
    assert enriched[1]["resolved"]["kpi"]["value"] == 13.9
    assert enriched[2]["resolved"]["chart"]["points"][0]["value"] == 13.9



def test_enrich_input_overrides_source_date_range_preset():
    """Input periodDays/end_date acima de dateRangePreset this_month da fonte."""
    reset_comunicado_data_block_cache()
    gateway = MagicMock()
    gateway.fetch_by_operation_id.return_value = {
        "meta": {"operationId": "get_production_oee_series", "shape": "series"},
        "data": {"points": [{"date": "2026-07-11", "value": 90}]},
        "route": {
            "label": "OEE — série temporal",
            "paramStrategy": "direct",
            "paramSchema": {
                "start_date": {"type": "string", "format": "date"},
                "end_date": {"type": "string", "format": "date", "label": "Data fim"},
                "periodDays": {"type": "integer", "label": "Período (dias)"},
                "branch": {"type": "string", "label": "Filial"},
            },
            "tvConstraints": {},
        },
    }
    service = ComunicadoDataEnrichmentService(
        catalog=TvDataRouteCatalogService(),
        gateway=gateway,
    )
    source = {
        "id": "src-oee",
        "type": "data_source",
        "dataBinding": {
            "operationId": "get_production_oee_series",
            "displayMode": "chart",
            "params": {"dateRangePreset": "this_month"},
        },
    }
    cfg = {
        "blocks": [
            source,
            {
                "id": "inp-period",
                "type": "input",
                "input": {
                    "paramKey": "periodDays",
                    "defaultValue": 4,
                    "targetScope": "sources",
                    "targetSourceIds": ["src-oee"],
                },
            },
        ]
    }
    service.enrich_blocks([source], cfg=cfg, authorization="Bearer x")
    params = gateway.fetch_by_operation_id.call_args.kwargs["params"]
    assert params.get("periodDays") == 4
    assert "dateRangePreset" not in params


def test_enrich_preview_applies_input_from_cfg_blocks():
    """POST /data/preview-block envia só a fonte em `blocks`; inputs vêm em nativeConfig.blocks."""
    reset_comunicado_data_block_cache()
    gateway = MagicMock()
    gateway.fetch_by_operation_id.return_value = {
        "meta": {"operationId": "get_production_allocation_gaps", "shape": "playbook_report"},
        "data": {"items": [{"branch": "01", "component_code": "X"}]},
        "route": {
            "label": "Componentes sem empenho (travamento)",
            "tableFields": "items",
            "tvConstraints": {},
        },
    }
    service = ComunicadoDataEnrichmentService(
        catalog=TvDataRouteCatalogService(),
        gateway=gateway,
    )
    source = {
        "id": "src-gaps",
        "type": "data_source",
        "dataBinding": {
            "operationId": "get_production_allocation_gaps",
            "displayMode": "table",
        },
    }
    cfg = {
        "blocks": [
            source,
            {
                "id": "inp-branch",
                "type": "input",
                "input": {
                    "paramKey": "branch",
                    "defaultValue": "01",
                    "targetScope": "sources",
                    "targetSourceIds": ["src-gaps"],
                },
            },
        ]
    }
    enriched = service.enrich_blocks([source], cfg=cfg, authorization="Bearer x")
    assert gateway.fetch_by_operation_id.call_args.kwargs["params"]["branch"] == "01"
    assert enriched[0]["resolved"]["table"]["rows"]


def test_enrich_multi_metric_lmp_summary_all_and_selected():
    reset_comunicado_data_block_cache()
    gateway = MagicMock()
    gateway.fetch_by_operation_id.return_value = {
        "meta": {"operationId": "get_lmps_dashboard_summary", "shape": "scalar"},
        "data": {
            "summary": {
                "total_lmps": 42,
                "percent_dentro_prazo": 81.5,
                "avg_lead_time": 3.2,
                "total_items": 120,
            }
        },
        "route": {
            "label": "KPIs LMP",
            "valueFields": [
                "total_lmps",
                "percent_dentro_prazo",
                "avg_lead_time",
                "total_items",
            ],
            "valueFieldLabels": {
                "total_lmps": "Total de LMPs",
                "percent_dentro_prazo": "% no prazo",
                "avg_lead_time": "Lead time médio",
                "total_items": "Total de itens",
            },
            "tvConstraints": {},
        },
    }
    service = ComunicadoDataEnrichmentService(
        catalog=TvDataRouteCatalogService(),
        gateway=gateway,
    )
    all_metrics = service.enrich_blocks(
        [
            {
                "id": "src-all",
                "type": "data_source",
                "dataBinding": {
                    "operationId": "get_lmps_dashboard_summary",
                    "displayMode": "kpi",
                },
            }
        ],
        cfg={},
        authorization="Bearer x",
    )
    metrics = all_metrics[0]["resolved"]["kpiMetrics"]
    assert len(metrics) == 4
    assert metrics[0]["field"] == "total_lmps"
    assert metrics[0]["value"] == 42
    assert all_metrics[0]["resolved"]["kpi"]["value"] == 42
    assert len(all_metrics[0]["resolved"]["chart"]["points"]) == 4
    assert len(all_metrics[0]["resolved"]["table"]["rows"]) == 4

    selected = service.enrich_blocks(
        [
            {
                "id": "src-sel",
                "type": "data_source",
                "dataBinding": {
                    "operationId": "get_lmps_dashboard_summary",
                    "displayMode": "kpi",
                    "selectedValueFields": ["percent_dentro_prazo", "total_items"],
                },
            }
        ],
        cfg={},
        authorization="Bearer x",
    )
    selected_metrics = selected[0]["resolved"]["kpiMetrics"]
    assert [item["field"] for item in selected_metrics] == [
        "percent_dentro_prazo",
        "total_items",
    ]
    assert selected[0]["resolved"]["kpi"]["value"] == 81.5
    assert selected[0]["resolved"]["kpi"]["label"] == "% no prazo"


def test_decorate_input_resolves_branch_from_slide_schemas():
    gateway = MagicMock()
    service = ComunicadoDataEnrichmentService(
        catalog=TvDataRouteCatalogService(),
        gateway=gateway,
    )
    enriched = service.enrich_blocks(
        [
            {
                "id": "src-1",
                "type": "data_source",
                "dataBinding": {
                    "operationId": "get_production_oee_series",
                    "displayMode": "chart",
                },
            },
            {
                "id": "input-1",
                "type": "input",
                "input": {
                    "paramKey": "branch",
                    "label": "Filial",
                    "targetScope": "slide",
                },
            },
        ],
        cfg={},
        authorization="Bearer x",
    )
    input_block = next(item for item in enriched if item["id"] == "input-1")
    assert input_block["input"]["paramAvailable"] is True
    assert input_block["input"]["resolvedField"]["type"]


def test_decorate_input_ignores_empty_source_schemas_and_keeps_param():
    """Escopo sources: schema {} não zera a interseção (paridade editor)."""
    gateway = MagicMock()
    service = ComunicadoDataEnrichmentService(
        catalog=TvDataRouteCatalogService(),
        gateway=gateway,
    )
    enriched = service.enrich_blocks(
        [
            {
                "id": "src-ok",
                "type": "data_source",
                "dataBinding": {
                    "operationId": "get_production_oee_series",
                    "displayMode": "chart",
                },
            },
            {
                "id": "src-empty",
                "type": "data_source",
                "dataBinding": {
                    "operationId": "",
                    "displayMode": "chart",
                },
            },
            {
                "id": "input-1",
                "type": "input",
                "input": {
                    "paramKey": "branch",
                    "label": "Filial",
                    "targetScope": "sources",
                    "targetSourceIds": ["src-ok", "src-empty"],
                },
            },
        ],
        cfg={},
        authorization="Bearer x",
    )
    input_block = next(item for item in enriched if item["id"] == "input-1")
    assert input_block["input"]["paramAvailable"] is True
    assert input_block["input"]["resolvedField"]["label"] == "Filial"
    assert input_block["input"]["resolvedField"]["type"] == "string"


def test_decorate_input_fallback_when_param_key_without_schemas():
    gateway = MagicMock()
    service = ComunicadoDataEnrichmentService(
        catalog=TvDataRouteCatalogService(),
        gateway=gateway,
    )
    enriched = service.enrich_blocks(
        [
            {
                "id": "input-1",
                "type": "input",
                "input": {"paramKey": "branch", "label": "Filial", "targetScope": "slide"},
            },
        ],
        cfg={},
        authorization="Bearer x",
    )
    input_block = enriched[0]
    assert input_block["input"]["paramAvailable"] is True
    assert input_block["input"]["resolvedField"]["type"] == "string"
    assert input_block["input"]["resolvedField"]["label"] == "Filial"
