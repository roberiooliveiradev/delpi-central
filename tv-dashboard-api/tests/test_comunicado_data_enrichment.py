from unittest.mock import MagicMock

from tv_app.application.services.comunicado_data_enrichment_service import (
    ComunicadoDataEnrichmentService,
    _apply_incremental_pagination_defaults,
    _extract_scalar_value,
    _extract_series,
    _source_table_for_route,
    reset_comunicado_data_block_cache,
)
from tv_app.application.services.tv_data_route_catalog_service import TvDataRouteCatalogService


def test_incremental_pagination_defaults_only_for_paginated_routes():
    route = {
        "paramSchema": {
            "page": {"type": "integer"},
            "page_size": {"type": "integer"},
        }
    }
    assert _apply_incremental_pagination_defaults({}, route) == {
        "page": 1,
        "page_size": 30,
    }
    assert _apply_incremental_pagination_defaults(
        {"page": 3, "page_size": 15},
        route,
    ) == {"page": 3, "page_size": 15}
    assert _apply_incremental_pagination_defaults({}, {"paramSchema": {}}) == {}


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


def test_enrich_dashboard_department_indicators_unwraps_item_wrapper():
    """Ponte SI devolve `{ item: { idd, indicators } }` — preview TV precisa do IDD e da tabela."""
    gateway = MagicMock()
    gateway.fetch_by_operation_id.return_value = {
        "meta": {
            "operationId": "get_dashboard_department_indicators",
            "shape": "playbook_report",
        },
        "data": {
            "item": {
                "department_id": "commercial",
                "idd": 8.1,
                "score": 8.1,
                "indicators": [
                    {
                        "indicator_id": "commercial.otd",
                        "name": "OTD",
                        "score": 7.5,
                        "goals": {"consolidated": 95.0},
                        "realized": {"consolidated": 92.0},
                    }
                ],
            }
        },
        "route": {
            "label": "Departamento — IDD, metas e realizado",
            "valueFields": ["idd", "score"],
            "tableFields": "indicators",
            "allowedDisplayModes": ["kpi", "table", "auto"],
            "tvConstraints": {"maxRows": 20},
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
                "operationId": "get_dashboard_department_indicators",
                "params": {"department_id": "commercial"},
                "displayMode": "auto",
            },
        }
    ]
    enriched = service.enrich_blocks(blocks, cfg={}, authorization="Bearer x")
    resolved = enriched[0]["resolved"]
    assert resolved["kpi"]["value"] == 8.1
    assert resolved["table"]["rows"]
    assert resolved["table"]["rows"][0]["indicator_id"] == "commercial.otd"


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


def test_enrich_table_accepts_bare_list_payload_like_eficiencia_appointments():
    """api-delpi bulk appointments devolve data=[...] (não {items:[...]}); preview TV precisa mapear."""
    reset_comunicado_data_block_cache()
    gateway = MagicMock()
    gateway.fetch_by_operation_id.return_value = {
        "meta": {
            "operationId": "list_eficiencia_fabril_appointments",
            "shape": "paged_list",
        },
        "data": [
            {
                "appointment_id": "A1",
                "op": "OP001",
                "produto": "90010001",
                "centro_trabalho": "CT01",
            },
            {
                "appointment_id": "A2",
                "op": "OP002",
                "produto": "90010002",
                "centro_trabalho": "CT02",
            },
        ],
        "route": {
            "label": "Eficiência fabril — apontamentos (carga bulk)",
            "metaShape": "paged_list",
            "tvConstraints": {"maxRows": 5},
        },
    }
    service = ComunicadoDataEnrichmentService(
        catalog=TvDataRouteCatalogService(),
        gateway=gateway,
    )
    enriched = service.enrich_blocks(
        [
            {
                "id": "tbl-bulk",
                "type": "data_source",
                "dataBinding": {
                    "operationId": "list_eficiencia_fabril_appointments",
                    "displayMode": "table",
                },
            }
        ],
        cfg={},
        authorization="Bearer x",
    )
    rows = enriched[0]["resolved"]["table"]["rows"]
    assert len(rows) == 2
    assert rows[0]["appointment_id"] == "A1"
    assert rows[1]["op"] == "OP002"
    columns = enriched[0]["resolved"]["table"]["columns"]
    assert any(column["key"] == "appointment_id" for column in columns)


def test_enrich_kpi_discovers_fields_when_catalog_value_fields_miss_payload():
    """Catálogo gerado às vezes usa valueFields fantasma; discovery deve preencher o KPI."""
    reset_comunicado_data_block_cache()
    gateway = MagicMock()
    gateway.fetch_by_operation_id.return_value = {
        "meta": {"operationId": "get_branch_rol_target_pct", "shape": "scalar"},
        "data": {
            "branch": "02",
            "rol": 1000.0,
            "target": 900.0,
            "rol_target_pct": 111.1,
        },
        "route": {
            "label": "Meta ROL",
            "valueFields": ["branch_rol_target_pct", "value"],
            "tvConstraints": {},
        },
    }
    service = ComunicadoDataEnrichmentService(
        catalog=TvDataRouteCatalogService(),
        gateway=gateway,
    )
    enriched = service.enrich_blocks(
        [
            {
                "id": "kpi-1",
                "type": "data_source",
                "dataBinding": {
                    "operationId": "get_branch_rol_target_pct",
                    "displayMode": "kpi",
                },
            }
        ],
        cfg={},
        authorization="Bearer x",
    )
    metrics = enriched[0]["resolved"]["kpiMetrics"]
    fields = {metric["field"] for metric in metrics}
    assert "rol_target_pct" in fields
    assert enriched[0]["resolved"]["kpi"]["value"] is not None


def test_enrich_si_scalar_meta_prefers_value_not_alias_metrics():
    """SI meta devolve value + comparable_goal + goal_value iguais — KPI deve ser um só."""
    reset_comunicado_data_block_cache()
    gateway = MagicMock()
    gateway.fetch_by_operation_id.return_value = {
        "meta": {
            "operationId": "get_si_indicator_quality_ppm_external_meta",
            "shape": "scalar",
            "entity": "dashboard_si_indicator_meta",
        },
        "data": {
            "indicator_id": "quality-ppm-external",
            "name": "PPM Externo",
            "value": 1100.0,
            "comparable_goal": 1100.0,
            "goal_value": 1100.0,
            "value_decimals": 2,
            "has_value": True,
        },
        "route": {
            "label": "PPM Externo — meta",
            "metaShape": "scalar",
            "valueFields": ["value"],
            "tvConstraints": {"maxRows": 1},
        },
    }
    service = ComunicadoDataEnrichmentService(
        catalog=TvDataRouteCatalogService(),
        gateway=gateway,
    )
    enriched = service.enrich_blocks(
        [
            {
                "id": "si-1",
                "type": "data_source",
                "dataBinding": {
                    "operationId": "get_si_indicator_quality_ppm_external_meta",
                    "displayMode": "kpi",
                },
            }
        ],
        cfg={},
        authorization="Bearer x",
    )
    metrics = enriched[0]["resolved"]["kpiMetrics"]
    assert len(metrics) == 1
    assert metrics[0]["field"] == "value"
    assert metrics[0]["value"] == 1100.0
    assert enriched[0]["resolved"]["kpi"]["value"] == 1100.0
    assert "table" not in enriched[0]["resolved"] or not enriched[0]["resolved"].get("table")


def test_enrich_table_reads_branches_and_ranking_list_keys():
    reset_comunicado_data_block_cache()
    gateway = MagicMock()
    gateway.fetch_by_operation_id.return_value = {
        "meta": {"operationId": "list_hr_branches", "shape": "scalar"},
        "data": {"branches": ["01", "02"]},
        "route": {"label": "Filiais RH", "tvConstraints": {"maxRows": 10}},
    }
    service = ComunicadoDataEnrichmentService(
        catalog=TvDataRouteCatalogService(),
        gateway=gateway,
    )
    enriched = service.enrich_blocks(
        [
            {
                "id": "br-1",
                "type": "data_source",
                "dataBinding": {"operationId": "list_hr_branches", "displayMode": "table"},
            }
        ],
        cfg={},
        authorization="Bearer x",
    )
    rows = enriched[0]["resolved"]["table"]["rows"]
    assert len(rows) == 2
    assert rows[0]["value"] == "01"


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


def test_enrich_series_route_does_not_leak_internal_metadata_as_table():
    """Regressão prod: OEE série (points + granularity/truncated) deve virar tabela de série,
    nunca campo/valor com metadados internos (granularity, truncated)."""
    reset_comunicado_data_block_cache()
    gateway = MagicMock()
    gateway.fetch_by_operation_id.return_value = {
        "meta": {"operationId": "get_production_oee_series", "shape": "playbook_report"},
        "data": {
            "granularity": "day",
            "truncated": False,
            "branch": "01",
            "points": [
                {
                    "periodo": "2026-07-01",
                    "sort_key": "2026-07-01",
                    "date_start": "2026-07-01",
                    "date_end": "2026-07-01",
                    "oee_filial_01": 82.5,
                    "oee_filial_02": None,
                },
                {
                    "periodo": "2026-07-02",
                    "sort_key": "2026-07-02",
                    "date_start": "2026-07-02",
                    "date_end": "2026-07-02",
                    "oee_filial_01": 84.0,
                    "oee_filial_02": None,
                },
            ],
        },
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
                "params": {"branch": "01", "periodDays": 30},
                "displayMode": "auto",
            },
        }
    ]
    enriched = service.enrich_blocks(blocks, cfg={}, authorization="Bearer x")
    table = enriched[0]["resolved"]["table"]
    column_keys = {col["key"] for col in table["columns"]}
    assert column_keys == {"periodo", "value"}
    assert "campo" not in column_keys and "valor" not in column_keys
    # Linhas só com as chaves declaradas — sem `label` duplicando a coluna Período.
    assert all(set(row.keys()) == {"periodo", "value"} for row in table["rows"])
    assert [row["value"] for row in table["rows"]] == [82.5, 84.0]
    assert enriched[0]["resolved"]["kpi"]["value"] == 84.0


def test_enrich_series_route_empty_points_yields_no_metadata_rows():
    """Série vazia não deve vazar granularity/truncated como campo/valor."""
    reset_comunicado_data_block_cache()
    gateway = MagicMock()
    gateway.fetch_by_operation_id.return_value = {
        "meta": {"operationId": "get_production_oee_series", "shape": "playbook_report"},
        "data": {"granularity": "day", "truncated": False, "branch": "01", "points": []},
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
                "params": {"branch": "01", "periodDays": 30},
                "displayMode": "table",
            },
        }
    ]
    enriched = service.enrich_blocks(blocks, cfg={}, authorization="Bearer x")
    table = enriched[0]["resolved"]["table"]
    assert table["rows"] == []
    serialized = str(table)
    assert "granularity" not in serialized and "truncated" not in serialized


def test_source_table_for_series_route_uses_normalized_points():
    """Fonte do M em rota de série = periodo/value (nunca campo/valor de metadados)."""
    data = {
        "granularity": "day",
        "truncated": False,
        "points": [
            {"periodo": "2026-07-01", "oee_filial_01": 82.5},
            {"periodo": "2026-07-02", "oee_filial_01": 84.0},
        ],
    }
    route_info = {"seriesField": "points", "label": "OEE — série temporal"}
    table = _source_table_for_route(data, route_info, branch="01")
    assert table is not None
    assert table["columns"] == ["periodo", "value"]
    assert [row["value"] for row in table["rows"]] == [82.5, 84.0]
    assert "campo" not in table["columns"] and "valor" not in table["columns"]


def test_source_table_for_non_series_route_defers_to_generic_coerce():
    """Sem seriesField, retorna None para o executor usar o coerce genérico."""
    assert _source_table_for_route({"items": [{"a": 1}]}, {"shape": "list"}) is None
    assert _source_table_for_route({"a": 1}, None) is None


def test_enrich_series_route_with_m_transform_preview_uses_series_table():
    """Regressão prod: preview do M em rota de série mostra periodo/value, não os
    metadados internos (granularity/truncated) como campo/valor."""
    reset_comunicado_data_block_cache()
    gateway = MagicMock()
    gateway.fetch_by_operation_id.return_value = {
        "meta": {"operationId": "get_production_oee_series", "shape": "playbook_report"},
        "data": {
            "granularity": "day",
            "truncated": False,
            "branch": "01",
            "points": [
                {"periodo": "2026-07-01", "oee_filial_01": 82.5, "oee_filial_02": None},
                {"periodo": "2026-07-02", "oee_filial_01": 84.0, "oee_filial_02": None},
            ],
        },
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
                "params": {"branch": "01", "periodDays": 30},
                "displayMode": "table",
            },
            "dataTransform": {
                "version": 2,
                "language": "m-delpi-v1",
                "script": "let\n    FonteSemEtapas = Table.Skip(Fonte, 0)\nin\n    FonteSemEtapas",
            },
        }
    ]
    enriched = service.enrich_blocks(blocks, cfg={}, authorization="Bearer x")
    resolved = enriched[0]["resolved"]
    # Preview consumido pelo modal Preparar dados: periodo/value, nunca campo/valor.
    preview = resolved.get("preview")
    assert isinstance(preview, dict)
    preview_keys = [col["key"] for col in preview["columns"]]
    assert preview_keys == ["periodo", "value"]
    assert [col["key"] for col in preview["sourceColumns"]] == [
        "periodo",
        "value",
    ]
    assert "campo" not in preview_keys and "valor" not in preview_keys
    assert [row["value"] for row in preview["rows"]] == [82.5, 84.0]
    # Apresentação (mesmo fluxo do gráfico/tabela) continua renderizando a série
    # transformada, não uma tabela vazia.
    table = resolved.get("table")
    assert isinstance(table, dict) and table["rows"]
    assert [row.get("value") for row in table["rows"]] == [82.5, 84.0]
    # Nenhum metadado interno vaza como coluna/linha dos dados.
    table_column_keys = {col["key"] for col in table["columns"]}
    assert not ({"granularity", "truncated", "campo", "valor"} & table_column_keys)
    assert all(
        set(row.keys()) <= {"periodo", "value"} for row in preview["rows"]
    )


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


def test_enrich_kpi_skips_total_records_and_attaches_playbook_table():
    reset_comunicado_data_block_cache()
    gateway = MagicMock()
    gateway.fetch_by_operation_id.return_value = {
        "meta": {
            "operationId": "get_production_consumption_top_items_by_work_center",
            "shape": "playbook_report",
            "fields": [
                {"key": "item_code", "label": "Código"},
                {"key": "real_consumption_qty", "label": "Consumo"},
            ],
        },
        "data": {
            "items": [
                {"item_code": "1001", "real_consumption_qty": 12.5},
                {"item_code": "1002", "real_consumption_qty": 8.0},
            ],
            "summary": {
                "total_records": 10,
                "is_complete": True,
                "consolidated_across_branches": True,
            },
        },
        "route": {
            "label": "Consumo por centro de trabalho",
            "tvConstraints": {},
        },
    }
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
                    "operationId": "get_production_consumption_top_items_by_work_center",
                    "displayMode": "kpi",
                },
            }
        ],
        cfg={},
        authorization="Bearer x",
    )
    resolved = enriched[0]["resolved"]
    assert len(resolved["kpiMetrics"]) == 1
    assert resolved["kpiMetrics"][0]["field"] == "total_records"
    assert resolved["kpiMetrics"][0]["value"] == 10
    assert resolved["kpi"]["value"] == 10
    assert len(resolved["table"]["rows"]) == 2
    assert resolved["table"]["rows"][0]["item_code"] == "1001"


def test_enrich_allocation_gaps_kpi_uses_list_count():
    reset_comunicado_data_block_cache()
    gateway = MagicMock()
    gateway.fetch_by_operation_id.return_value = {
        "meta": {"operationId": "get_production_allocation_gaps", "shape": "playbook_report"},
        "data": {
            "items": [
                {"branch": "02", "component_code": "1001", "allocated_qty": 0.0},
                {"branch": "02", "component_code": "1002", "allocated_qty": 0.0},
            ],
            "summary": {"total_records": 42, "is_complete": False},
        },
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
    enriched = service.enrich_blocks(
        [
            {
                "id": "src-1",
                "type": "data_source",
                "dataBinding": {
                    "operationId": "get_production_allocation_gaps",
                    "displayMode": "kpi",
                },
            }
        ],
        cfg={},
        authorization="Bearer x",
    )
    resolved = enriched[0]["resolved"]
    assert resolved["kpi"]["value"] == 42
    assert resolved["kpiMetrics"][0]["label"] == "Quantidade"
    assert len(resolved["table"]["rows"]) == 2


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


def test_enrich_auto_resolves_table_for_text_only_list_shape():
    reset_comunicado_data_block_cache()
    gateway = MagicMock()
    gateway.fetch_by_operation_id.return_value = {
        "meta": {"operationId": "get_lmp_history_flow", "shape": "list"},
        "data": {
            "flow": [
                {"status": "APROVADO", "usuario": "Ana", "data": "2026-07-01"},
                {"status": "PENDENTE", "usuario": "Bruno", "data": "2026-07-02"},
            ]
        },
        "route": {
            "label": "Transições de fluxo",
            "metaShape": "list",
            "tvConstraints": {"maxRows": 10},
        },
    }
    service = ComunicadoDataEnrichmentService(
        catalog=TvDataRouteCatalogService(),
        gateway=gateway,
    )
    enriched = service.enrich_blocks(
        [
            {
                "id": "flow-1",
                "type": "data_metric",
                "dataBinding": {
                    "operationId": "get_lmp_history_flow",
                    "displayMode": "auto",
                },
            }
        ],
        cfg={},
        authorization="Bearer x",
    )
    rows = enriched[0]["resolved"]["table"]["rows"]
    assert len(rows) == 2
    assert rows[0]["status"] == "APROVADO"


def test_enrich_auto_resolves_table_for_text_only_scalar_object():
    reset_comunicado_data_block_cache()
    gateway = MagicMock()
    gateway.fetch_by_operation_id.return_value = {
        "meta": {"operationId": "list_hr_branches", "shape": "scalar"},
        "data": {"status": "ATIVO", "owner": "Operações"},
        "route": {
            "label": "Status",
            "metaShape": "scalar",
            "tvConstraints": {"maxRows": 10},
        },
    }
    service = ComunicadoDataEnrichmentService(
        catalog=TvDataRouteCatalogService(),
        gateway=gateway,
    )
    enriched = service.enrich_blocks(
        [
            {
                "id": "status-1",
                "type": "data_table",
                "dataBinding": {
                    "operationId": "list_hr_branches",
                    "displayMode": "auto",
                },
            }
        ],
        cfg={},
        authorization="Bearer x",
    )
    rows = enriched[0]["resolved"]["table"]["rows"]
    assert len(rows) >= 2
    assert any(row.get("valor") == "ATIVO" for row in rows)


def test_enrich_unwraps_api_delpi_envelope_for_text_list():
    reset_comunicado_data_block_cache()
    gateway = MagicMock()
    gateway.fetch_by_operation_id.return_value = {
        "meta": {"operationId": "list_hr_branches", "shape": "list"},
        "data": {
            "success": True,
            "data": {
                "records": [
                    {"codigo": "A1", "descricao": "Item A"},
                    {"codigo": "A2", "descricao": "Item B"},
                ]
            },
        },
        "route": {
            "label": "Registros",
            "metaShape": "list",
            "tvConstraints": {"maxRows": 10},
        },
    }
    service = ComunicadoDataEnrichmentService(
        catalog=TvDataRouteCatalogService(),
        gateway=gateway,
    )
    enriched = service.enrich_blocks(
        [
            {
                "id": "records-1",
                "type": "data_table",
                "dataBinding": {
                    "operationId": "list_hr_branches",
                    "displayMode": "table",
                },
            }
        ],
        cfg={},
        authorization="Bearer x",
    )
    rows = enriched[0]["resolved"]["table"]["rows"]
    assert len(rows) == 2
    assert rows[0]["codigo"] == "A1"


def test_enrich_links_text_block_to_data_source_resolved():
    reset_comunicado_data_block_cache()
    gateway = MagicMock()
    gateway.fetch_by_operation_id.return_value = {
        "meta": {"operationId": "get_branch_rol_target_pct", "shape": "scalar"},
        "data": {
            "branch": "02",
            "rol_target_pct": 111.1,
        },
        "route": {
            "label": "Meta ROL",
            "valueFields": ["rol_target_pct"],
            "tvConstraints": {},
        },
    }
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
                    "operationId": "get_branch_rol_target_pct",
                    "displayMode": "kpi",
                },
            },
            {
                "id": "txt-1",
                "type": "text",
                "content": "—",
                "dataSourceId": "src-1",
                "textProjection": {"field": "rol_target_pct", "format": "number"},
                "frame": {"x": 0, "y": 0, "w": 20, "h": 10},
            },
        ],
        cfg={},
        authorization="Bearer x",
    )
    source = next(b for b in enriched if b.get("id") == "src-1")
    text = next(b for b in enriched if b.get("id") == "txt-1")
    assert source.get("resolved", {}).get("kpi", {}).get("value") is not None
    assert text.get("resolved", {}).get("kpi", {}).get("value") is not None
    assert text.get("serverTextProjectionApplied") is True


def test_enrich_blocks_links_resolved_to_canvas_table():
    """Grade com dataSourceId (bloco e/ou célula) recebe resolvedBySourceId."""
    reset_comunicado_data_block_cache()
    gateway = MagicMock()

    def _fetch(operation_id: str, **kwargs):
        if operation_id == "get_ppm_meta":
            return {
                "meta": {"operationId": "get_ppm_meta", "shape": "scalar"},
                "data": {"ppm": 1400},
                "route": {
                    "label": "PPM meta",
                    "valueFields": ["ppm"],
                    "tvConstraints": {},
                },
            }
        return {
            "meta": {"operationId": "get_branch_rol_target_pct", "shape": "scalar"},
            "data": {
                "branch": "02",
                "rol_target_pct": 111.1,
                "meta": 120.0,
            },
            "route": {
                "label": "Meta ROL",
                "valueFields": ["rol_target_pct", "meta"],
                "tvConstraints": {},
            },
        }

    gateway.fetch_by_operation_id.side_effect = _fetch
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
                    "operationId": "get_branch_rol_target_pct",
                    "displayMode": "kpi",
                },
            },
            {
                "id": "src-meta",
                "type": "data_source",
                "dataBinding": {
                    "operationId": "get_ppm_meta",
                    "displayMode": "kpi",
                },
            },
            {
                "id": "grade-1",
                "type": "canvas_table",
                "rows": 3,
                "cols": 2,
                "cells": [
                    [{"kind": "text", "text": "KPI"}, {"kind": "text", "text": "Valor"}],
                    [
                        {"kind": "text", "text": "Realizado"},
                        {
                            "kind": "number",
                            "dataSourceId": "src-1",
                            "dataRef": {"field": "rol_target_pct", "format": "number"},
                        },
                    ],
                    [
                        {"kind": "text", "text": "Meta"},
                        {
                            "kind": "number",
                            "dataSourceId": "src-meta",
                            "dataRef": {"field": "ppm", "format": "number"},
                        },
                    ],
                ],
                "frame": {"x": 0, "y": 0, "w": 40, "h": 20},
            },
        ],
        cfg={},
        authorization="Bearer x",
    )
    grade = next(b for b in enriched if b.get("id") == "grade-1")
    by_source = grade.get("resolvedBySourceId") or {}
    assert "src-1" in by_source
    assert "src-meta" in by_source
    assert grade.get("serverCanvasTableProjectionApplied") is True
    body_refs = [
        (cell.get("dataSourceId"), cell.get("dataRef", {}).get("field"))
        for row in grade.get("cells", [])[1:]
        for cell in row
        if cell.get("dataRef", {}).get("field")
    ]
    assert body_refs == [("src-1", "rol_target_pct"), ("src-meta", "ppm")]


def test_enrich_kpi_uses_meta_fields_dict_labels_pt():
    """meta.fields dict (api-delpi) rotula kpiMetrics — picker Campo dinâmico em PT."""
    reset_comunicado_data_block_cache()
    gateway = MagicMock()
    gateway.fetch_by_operation_id.return_value = {
        "meta": {
            "operationId": "get_quality_scrap_cost_pct",
            "shape": "scalar",
            "fields": {
                "scrap_cost_pct": "Custo de refugo / ROL (%)",
                "scrap_cost": "Custo de refugo (R$)",
                "rol_with_ipi": "ROL com IPI (R$)",
                "occurrences": "Ocorrências de refugo",
                "value": "Valor",
            },
        },
        "data": {
            "scrap_cost_pct": 0.57,
            "scrap_cost": 1200.0,
            "rol_with_ipi": 210_000.0,
            "occurrences": 3,
            "value": 0.57,
        },
        "route": {
            "label": "Custo de refugo / ROL",
            "valueFields": ["scrap_cost_pct", "value"],
            "valueFieldLabels": {},
            "tvConstraints": {},
        },
    }
    service = ComunicadoDataEnrichmentService(
        catalog=TvDataRouteCatalogService(),
        gateway=gateway,
    )
    blocks = service.enrich_blocks(
        [
            {
                "id": "src-1",
                "type": "data_source",
                "dataBinding": {
                    "operationId": "get_quality_scrap_cost_pct",
                    "displayMode": "kpi",
                },
            }
        ],
        cfg={},
        authorization="Bearer x",
    )
    metrics = {item["field"]: item["label"] for item in blocks[0]["resolved"]["kpiMetrics"]}
    assert metrics.get("scrap_cost_pct") == "Custo de refugo / ROL (%)"
    assert metrics.get("scrap_cost") == "Custo de refugo (R$)" or "scrap_cost" not in metrics
    assert blocks[0]["resolved"]["kpi"]["label"] == "Custo de refugo / ROL (%)"
