"""Hydrate de dataBindings ao catálogo vivo."""

from __future__ import annotations

from tv_app.application.services.data.tv_data_binding_hydrate_service import (
    hydrate_comunicado_data_bindings,
    hydrate_data_binding,
)
from tv_app.application.services.data.tv_data_param_validation_service import (
    validate_params_against_schema,
)


class _FakeCatalog:
    def __init__(self, routes: dict) -> None:
        self._routes = routes

    def get_route(self, operation_id: str):
        return self._routes.get(operation_id)


def test_hydrate_clears_catalog_like_label_and_remaps_dates():
    route = {
        "operationId": "get_ppm_internal_summary",
        "label": "PPM Interno — realizado",
        "labelAliases": ["Qualidade — PPM interno"],
        "paramSchema": {
            "start_date": {"type": "string"},
            "end_date": {"type": "string"},
            "branch": {"type": "string", "optional": True},
        },
    }
    binding, diag = hydrate_data_binding(
        {
            "operationId": "get_ppm_internal_summary",
            "label": "Qualidade — PPM interno",
            "params": {
                "date_start": "2026-01-01",
                "date_end": "2026-01-31",
                "legacy_junk": 1,
            },
        },
        route,
    )
    assert diag["clearedLabel"] is True
    assert "label" not in binding
    assert binding["params"]["start_date"] == "2026-01-01"
    assert binding["params"]["end_date"] == "2026-01-31"
    assert "date_start" not in binding["params"]
    assert "legacy_junk" not in binding["params"]
    assert "legacy_junk" in diag["strippedParams"]


def test_validate_params_strips_unknown_instead_of_raising():
    schema = {"branch": {"type": "string", "optional": True}}
    out = validate_params_against_schema(
        {"branch": "01", "gone": "x"},
        schema,
    )
    assert out == {"branch": "01"}


def test_hydrate_config_marks_orphan_route():
    catalog = _FakeCatalog(
        {
            "get_ok": {
                "label": "OK",
                "paramSchema": {"branch": {"type": "string", "optional": True}},
            }
        }
    )
    cfg, summary = hydrate_comunicado_data_bindings(
        {
            "blocks": [
                {
                    "id": "a",
                    "type": "data_source",
                    "dataBinding": {"operationId": "get_gone", "params": {}},
                },
                {
                    "id": "b",
                    "type": "data_source",
                    "dataBinding": {"operationId": "get_ok", "params": {"branch": "01"}},
                },
            ]
        },
        catalog=catalog,
    )
    assert summary["orphanOperationIds"] == ["get_gone"]
    assert len(cfg["blocks"]) == 2


def test_enrich_orphan_data_source_soft_fails_without_raising():
    from unittest.mock import MagicMock

    from tv_app.application.services.comunicado_data_enrichment_service import (
        ComunicadoDataEnrichmentService,
    )

    catalog = MagicMock()
    catalog.get_route.side_effect = lambda op: (
        {"operationId": "get_ok", "label": "OK", "paramSchema": {}, "valueFields": ["value"]}
        if op == "get_ok"
        else None
    )
    catalog.is_allowed.side_effect = lambda op: op == "get_ok"
    gateway = MagicMock()
    gateway.fetch_by_operation_id.return_value = {
        "meta": {"operationId": "get_ok", "shape": "scalar"},
        "data": {"summary": {"value": 1}},
        "route": {"label": "OK", "valueFields": ["value"], "tvConstraints": {}},
    }
    service = ComunicadoDataEnrichmentService(catalog=catalog, gateway=gateway)
    enriched = service.enrich_blocks(
        [
            {"id": "bad", "type": "data_source", "dataBinding": {"operationId": "get_gone", "params": {}}},
            {"id": "ok", "type": "data_source", "dataBinding": {"operationId": "get_ok", "params": {}}},
        ],
        cfg={},
        authorization="Bearer x",
    )
    assert "error" in (enriched[0].get("resolved") or {})
    assert enriched[1].get("resolved", {}).get("kpi", {}).get("value") == 1
