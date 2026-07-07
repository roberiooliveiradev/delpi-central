from unittest.mock import MagicMock

from tv_app.application.services.comunicado_data_enrichment_service import ComunicadoDataEnrichmentService
from tv_app.application.services.tv_data_route_catalog_service import TvDataRouteCatalogService


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
