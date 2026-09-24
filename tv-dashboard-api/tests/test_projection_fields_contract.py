"""Contrato projectableFields + contextFields (filtro efetivo)."""

from __future__ import annotations

from tv_app.application.services.comunicado_data_params_service import merge_data_params
from tv_app.application.services.data.projection_fields_contract import (
    CONTEXT_END,
    CONTEXT_RANGE_LABEL,
    CONTEXT_START,
    attach_projection_metadata,
    build_context_fields,
    build_projectable_fields,
    normalize_route_projectable_fields,
    validate_block_projection_fields,
)


def test_build_context_fields_custom_week_window():
    merged = merge_data_params(
        playlist_defaults={},
        slide_filters={
            "dateRangePreset": "custom",
            "start_date": "2026-09-21",
            "end_date": "2026-09-27",
        },
        block_params={},
    )
    fields, values = build_context_fields(merged)
    names = {item["name"] for item in fields}
    assert CONTEXT_START in names
    assert CONTEXT_END in names
    assert CONTEXT_RANGE_LABEL in names
    assert values[CONTEXT_START] == "2026-09-21"
    assert values[CONTEXT_END] == "2026-09-27"
    assert values[CONTEXT_RANGE_LABEL] == "21/09/2026 – 27/09/2026"


def test_build_context_fields_respects_layering_slide_over_playlist():
    merged = merge_data_params(
        playlist_defaults={"start_date": "2026-01-01", "end_date": "2026-01-31"},
        slide_filters={"start_date": "2026-09-21", "end_date": "2026-09-27"},
        block_params={},
        input_overrides=None,
    )
    _, values = build_context_fields(merged)
    assert values[CONTEXT_START] == "2026-09-21"
    assert values[CONTEXT_END] == "2026-09-27"


def test_build_projectable_fields_keeps_declared_when_dataset_empty():
    route = {
        "operationId": "get_otd_summary",
        "valueFields": ["otd_pct", "value"],
        "valueFieldTypes": {"otd_pct": "percent"},
        "valueFieldLabels": {"otd_pct": "OTD %"},
    }
    fields = build_projectable_fields(route, discovered_names=[])
    names = [item["name"] for item in fields]
    assert "otd_pct" in names
    assert "value" in names
    otd = next(item for item in fields if item["name"] == "otd_pct")
    assert otd["semanticType"] == "percent"
    assert otd["origin"] == "result"


def test_normalize_route_mirrors_value_fields_alias():
    route = normalize_route_projectable_fields(
        {
            "valueFields": ["forecast_value"],
            "valueFieldTypes": {"forecast_value": "currency"},
        }
    )
    assert route["projectableFields"][0]["name"] == "forecast_value"
    assert route["valueFields"] == ["forecast_value"]


def test_attach_projection_metadata_on_empty_resolved():
    resolved = attach_projection_metadata(
        {"meta": {}, "data": {}, "error": None},
        route={"valueFields": ["forecast_value", "realized_value"]},
        effective_params={"start_date": "2026-09-21", "end_date": "2026-09-27"},
        discovered_names=[],
    )
    assert {f["name"] for f in resolved["fields"]} >= {"forecast_value", "realized_value"}
    assert CONTEXT_START in resolved["contextValues"]
    assert any(f["name"] == CONTEXT_END for f in resolved["contextFields"])


def test_validate_invalid_projection_field():
    err = validate_block_projection_fields(
        {"textProjection": {"field": "nao_existe", "format": "raw"}},
        route={"valueFields": ["forecast_value", "value"]},
    )
    assert err is not None
    assert err["code"] == "INVALID_PROJECTION_FIELD"
    assert "nao_existe" in err["invalidFields"]
    assert "forecast_value" in err["allowedFields"]
    assert CONTEXT_START in err["allowedFields"]


def test_validate_preserves_filter_context_fields():
    err = validate_block_projection_fields(
        {
            "contentRuns": [
                {"text": "semana "},
                {"dataRef": {"field": CONTEXT_START, "format": "date"}},
                {"text": " – "},
                {"dataRef": {"field": CONTEXT_END, "format": "date"}},
            ]
        },
        route={"valueFields": ["otd_pct"]},
    )
    assert err is None


def test_validate_does_not_rewrite_valid_field():
    block = {"textProjection": {"field": CONTEXT_START, "format": "date"}}
    assert validate_block_projection_fields(block, route={"valueFields": ["value"]}) is None
    assert block["textProjection"]["field"] == CONTEXT_START
