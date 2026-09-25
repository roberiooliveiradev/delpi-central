"""Explicit table_view projection / frame authority + date precedence."""

from __future__ import annotations

from datetime import date

from tv_app.application.services.comunicado_data_params_service import merge_data_params
from tv_app.application.services.data.slide_layout_quality_service import (
    SlideLayoutQualityService,
)
from tv_app.application.services.data.table_view_projection_authority import (
    compare_explicit_block_intent,
    has_explicit_table_columns,
    normalize_block_table_projection,
    validate_table_parts,
)
from tv_app.application.services.data.tv_view_projection_service import (
    apply_view_projection_to_resolved,
)
from tv_app.application.services.data.visual_projection_service import (
    VisualProjectionService,
)
from tv_app.application.services.tv_date_range_preset_service import apply_date_range_preset


EXPLICIT_BLOCK = {
    "id": "wb_sc_table",
    "type": "table_view",
    "frame": {"x": 7, "y": 51, "w": 39, "h": 38},
    "tableProjection": {
        "columns": [
            {"field": "customer_name", "label": "Nome"},
            {"field": "forecast_value", "label": "Previsto", "valueFormat": "currency"},
            {"field": "realized_value", "label": "Realizado", "valueFormat": "currency"},
        ]
    },
}

SOURCE_RESOLVED = {
    "table": {
        "columns": [
            {"key": "customer_code", "label": "Customer código"},
            {"key": "customer_name", "label": "Customer nome"},
            {"key": "branch", "label": "Branch"},
            {"key": "forecast_value", "label": "Forecast valor"},
            {"key": "realized_value", "label": "Realized valor"},
            {"key": "variance_value", "label": "Variance valor"},
        ],
        "rows": [
            {
                "customer_code": "C1",
                "customer_name": "Acme",
                "branch": "01",
                "forecast_value": 100,
                "realized_value": 80,
                "variance_value": -20,
            }
        ],
    }
}


def test_normalize_field_alias_to_key():
    block = normalize_block_table_projection(dict(EXPLICIT_BLOCK))
    cols = block["tableProjection"]["columns"]
    assert [c["key"] for c in cols] == [
        "customer_name",
        "forecast_value",
        "realized_value",
    ]
    assert cols[0]["label"] == "Nome"


def test_explicit_projection_not_overwritten_by_route_inference():
    block = normalize_block_table_projection(dict(EXPLICIT_BLOCK))
    assert has_explicit_table_columns(block)
    route = {
        "valueFields": [
            "customer_code",
            "customer_name",
            "branch",
            "forecast_value",
            "realized_value",
            "variance_value",
        ]
    }
    next_block = VisualProjectionService.apply_to_block(block, route)
    keys = [c["key"] for c in next_block["tableProjection"]["columns"]]
    assert keys == ["customer_name", "forecast_value", "realized_value"]
    assert next_block["tableProjection"]["columns"][0]["label"] == "Nome"


def test_apply_view_projection_keeps_three_columns_and_labels():
    block = normalize_block_table_projection(dict(EXPLICIT_BLOCK))
    resolved = apply_view_projection_to_resolved(dict(SOURCE_RESOLVED), block)
    cols = resolved["table"]["columns"]
    assert [c["key"] for c in cols] == [
        "customer_name",
        "forecast_value",
        "realized_value",
    ]
    assert [c["label"] for c in cols] == ["Nome", "Previsto", "Realizado"]
    assert "variance_value" not in resolved["table"]["rows"][0]


def test_frame_intent_diff_detects_width_mutation():
    intent = normalize_block_table_projection(dict(EXPLICIT_BLOCK))
    actual = normalize_block_table_projection(
        {
            **EXPLICIT_BLOCK,
            "frame": {"x": 7, "y": 51, "w": 65, "h": 38},
            "tableProjection": {
                "columns": [
                    {"key": k, "label": lbl}
                    for k, lbl in [
                        ("customer_code", "Customer código"),
                        ("customer_name", "Customer nome"),
                        ("branch", "Branch"),
                        ("forecast_value", "Forecast valor"),
                        ("realized_value", "Realized valor"),
                        ("variance_value", "Variance valor"),
                    ]
                ]
            },
        }
    )
    diffs = compare_explicit_block_intent(intent_block=intent, actual_block=actual)
    paths = {d["path"] for d in diffs}
    assert "blocks.wb_sc_table.frame.w" in paths
    assert "blocks.wb_sc_table.tableProjection.columns" in paths


def test_side_by_side_tables_no_overlap_layout_gate():
    cfg = {
        "blocks": [
            {
                "id": "t1",
                "type": "table_view",
                "frame": {"x": 7, "y": 51, "w": 39, "h": 38},
            },
            {
                "id": "t2",
                "type": "table_view",
                "frame": {"x": 54, "y": 51, "w": 39, "h": 38},
            },
        ]
    }
    issues = SlideLayoutQualityService.collect_native_layout_issues(cfg)
    assert not any("overlap" in str(i) for i in issues)


def test_forced_overlap_when_width_mutated_to_65():
    cfg = {
        "blocks": [
            {
                "id": "t1",
                "type": "table_view",
                "frame": {"x": 7, "y": 51, "w": 65, "h": 38},
            },
            {
                "id": "t2",
                "type": "table_view",
                "frame": {"x": 54, "y": 51, "w": 65, "h": 38},
            },
        ]
    }
    issues = SlideLayoutQualityService.collect_native_layout_issues(cfg)
    assert issues, "mutated w=65 must fail layout gate"


def test_validate_table_parts_rejects_body_allows_row_banding():
    assert validate_table_parts({"body": {"visible": True}})
    assert not validate_table_parts(
        {
            "frame": {"visible": False},
            "rowEven": {"style": {"fill": "#06304D"}},
            "rowOdd": {"style": {"fill": "#0F527A"}},
        }
    )


def test_explicit_weekly_dates_win_over_this_month_preset():
    """Camada superior só com datas fecha a janela; preset herdado some."""
    merged = merge_data_params(
        playlist_defaults={"dateRangePreset": "this_month"},
        slide_filters=None,
        block_params={"start_date": "2026-09-21", "end_date": "2026-09-27"},
    )
    assert merged.get("start_date") == "2026-09-21"
    assert merged.get("end_date") == "2026-09-27"
    assert "dateRangePreset" not in merged

    # Sem preset relativo → datas manuais.
    resolved = apply_date_range_preset(
        {
            "start_date": "2026-09-21",
            "end_date": "2026-09-27",
        },
        schema_keys={"start_date": {}, "end_date": {}},
        strategy="date_range",
        today=date(2026, 9, 25),
    )
    assert resolved["start_date"] == "2026-09-21"
    assert resolved["end_date"] == "2026-09-27"


def test_same_layer_relative_preset_ignores_stale_absolute_dates():
    """Regressão «Este ano até hoje» com end_date D-1 escondido na UI."""
    merged = merge_data_params(
        playlist_defaults=None,
        slide_filters=None,
        block_params={
            "dateRangePreset": "this_year",
            "start_date": "2026-01-01",
            "end_date": "2026-09-24",
            "branch": "01",
        },
    )
    assert merged.get("dateRangePreset") == "this_year"
    assert "start_date" not in merged
    assert "end_date" not in merged

    resolved = apply_date_range_preset(
        {
            "dateRangePreset": "this_year",
            "start_date": "2026-01-01",
            "end_date": "2026-09-24",
        },
        schema_keys={"start_date": {}, "end_date": {}},
        strategy="date_range",
        today=date(2026, 9, 25),
    )
    assert resolved["start_date"] == "2026-01-01"
    assert resolved["end_date"] == "2026-09-25"
    assert "dateRangePreset" not in resolved


def test_monthly_fallback_without_explicit_dates():
    resolved = apply_date_range_preset(
        {"dateRangePreset": "this_month"},
        schema_keys={"start_date": {}, "end_date": {}},
        strategy="date_range",
        today=date(2026, 9, 24),
    )
    assert resolved["start_date"] == "2026-09-01"
    assert resolved["end_date"] == "2026-09-24"


def test_auto_inference_still_runs_without_explicit_columns():
    block = {"id": "t", "type": "table_view"}
    route = {"valueFields": ["a", "b", "c"], "valueFieldTypes": {"b": "currency"}}
    next_block = VisualProjectionService.apply_to_block(block, route)
    cols = next_block["tableProjection"]["columns"]
    assert [c["key"] for c in cols] == ["a", "b", "c"]
