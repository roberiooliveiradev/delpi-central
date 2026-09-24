"""G6/G23 — effectiveParams for presentation metadata."""

from tv_app.application.services.comunicado_data_enrichment_service import (
    _effective_params_for_presentation,
)
from tv_app.application.services.data.projection_fields_contract import (
    attach_projection_metadata,
    build_context_fields,
)


def test_effective_params_expands_this_month_preset():
    route = {
        "paramStrategy": "date_range",
        "paramSchema": {
            "start_date": {"type": "string"},
            "end_date": {"type": "string"},
            "dateRangePreset": {"type": "string"},
        },
        "dateRangeKeys": ["start_date", "end_date"],
    }
    out = _effective_params_for_presentation(
        {"dateRangePreset": "this_month"},
        route,
    )
    assert "dateRangePreset" not in out
    assert out.get("start_date")
    assert out.get("end_date")
    ctx_fields, ctx_values = build_context_fields(out)
    assert any(f.get("name") == "filter.start_date" for f in ctx_fields)
    assert "filter.start_date" in ctx_values
    assert "filter.end_date" in ctx_values


def test_attach_projection_metadata_with_presentation_params():
    route = {
        "paramStrategy": "date_range",
        "paramSchema": {
            "start_date": {"type": "string"},
            "end_date": {"type": "string"},
        },
        "dateRangeKeys": ["start_date", "end_date"],
        "valueFieldLabels": {"oee": "OEE"},
        "projectableFields": [{"name": "oee", "type": "number"}],
    }
    params = _effective_params_for_presentation(
        {"dateRangePreset": "last_7_days"},
        {
            **route,
            "paramSchema": {
                **route["paramSchema"],
                "dateRangePreset": {"type": "string"},
            },
        },
    )
    resolved = attach_projection_metadata(
        {"kpi": {"value": 1, "label": "x"}},
        route=route,
        effective_params=params,
        discovered_names=["oee"],
    )
    assert resolved["contextValues"]["filter.start_date"]
    assert resolved["contextValues"]["filter.end_date"]
