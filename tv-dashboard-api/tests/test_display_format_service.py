"""Corpus espelho de plugins/plugin-ui/src/displayFormat/formatDisplayValue.test.ts."""

from __future__ import annotations

from tv_app.application.services.data.display_format_service import (
    EMPTY_DISPLAY,
    DisplayFormatService,
    format_custom_pattern,
    parse_display_date,
)


def test_percent_canonical_does_not_multiply_by_100():
    assert DisplayFormatService.format_value(
        41.7, DisplayFormatService.spec_from_preset_id("percent")
    ) == "41,7%"
    assert (
        DisplayFormatService.format_value(
            41.7, {"category": "percent", "decimalPlaces": 0}
        )
        == "42%"
    )


def test_general_preserves_zero_padded_filial_codes():
    """Geral must not coerce filial 01/02 → 1/2 (FE-BE display ownership)."""
    general = {"category": "general", "presetId": "general", "locale": "pt-BR"}
    assert DisplayFormatService.format_value("01", general) == "01"
    assert DisplayFormatService.format_value("02", general) == "02"
    assert DisplayFormatService.format_value("1", general) == "1"
    assert DisplayFormatService.format_value(1, general) == "1"
    # Explicit number still coerces.
    assert DisplayFormatService.format_value("01", {"category": "number"}) == "1"
    assert DisplayFormatService.format_value("01", {"category": "text"}) == "01"


def test_iso_date_only_uses_utc_calendar():
    assert (
        DisplayFormatService.format_value(
            "2026-08-03", DisplayFormatService.spec_from_preset_id("date-short")
        )
        == "03/08/2026"
    )
    parsed = parse_display_date("2026-08-03")
    assert parsed is not None
    assert parsed["year"] == 2026
    assert parsed["month"] == 7
    assert parsed["day"] == 3
    assert parsed["dateOnly"] is True


def test_monthly_pt_api_label_not_date_parsed_as_2001():
    parsed = parse_display_date("Jan. de 26")
    assert parsed is not None
    assert parsed["year"] == 2026
    assert parsed["month"] == 0
    assert parsed["day"] == 1
    assert parsed["dateOnly"] is True

    fev = parse_display_date("Fev. de 26")
    assert fev is not None
    assert fev["year"] == 2026
    assert fev["month"] == 1

    assert (
        DisplayFormatService.format_value(
            "Jan. de 26", DisplayFormatService.spec_from_preset_id("date-short")
        )
        == "Jan. de 26"
    )
    assert (
        DisplayFormatService.format_value(
            "Fev. de 26", DisplayFormatService.spec_from_preset_id("date-short")
        )
        == "Fev. de 26"
    )


def test_custom_date_mask_mm_is_month_without_hh():
    assert format_custom_pattern("2026-08-03", "dd/mm/yyyy") == "03/08/2026"
    assert format_custom_pattern("2026-08-03T14:05:00", "HH:mm") == "14:05"
    assert (
        format_custom_pattern("2026-08-03T14:05:00", "dd/mm/yyyy HH:mm")
        == "03/08/2026 14:05"
    )


def test_custom_number_with_literal_brl():
    formatted = format_custom_pattern(30, '"R$" #.##0,00')
    assert formatted is not None
    assert "R$" in formatted
    assert "30,00" in formatted


def test_custom_empty_pattern_falls_back_via_format_value():
    assert DisplayFormatService.format_value(12, {"category": "custom", "pattern": ""}) == "12"


def test_number_without_explicit_places_does_not_pad_zeros():
    assert DisplayFormatService.format_value(12.5, {"category": "number"}) == "12,5"
    assert (
        DisplayFormatService.format_value(
            12.5, DisplayFormatService.resolve_spec(legacy_format="number", kind="chart")
        )
        == "12,5"
    )
    assert (
        DisplayFormatService.format_value(
            12.5,
            DisplayFormatService.resolve_spec(legacy_format="decimal", kind="canvas"),
        )
        == "12,5"
    )
    assert (
        DisplayFormatService.format_value(
            12.5,
            DisplayFormatService.resolve_spec(legacy_format="integer", kind="canvas"),
        )
        == "13"
    )
    assert (
        DisplayFormatService.format_value(
            12.5, DisplayFormatService.spec_from_preset_id("number-2")
        )
        == "12,50"
    )


def test_currency_brl_and_empty_display():
    formatted = DisplayFormatService.format_value(
        1234.5, DisplayFormatService.spec_from_preset_id("currency-brl")
    )
    assert formatted.startswith("R$")
    assert "1.234,50" in formatted
    assert DisplayFormatService.format_value(None, {"category": "number"}) == EMPTY_DISPLAY
    assert DisplayFormatService.format_value("", {"category": "number"}) == EMPTY_DISPLAY


def test_apply_to_resolved_text_projection_and_flag():
    resolved = {
        "kpi": {"value": 41.7, "label": "ROL"},
        "kpiMetrics": [{"field": "rol_target_pct", "label": "ROL", "value": 41.7}],
    }
    block = {
        "type": "text",
        "dataSourceId": "src-1",
        "textProjection": {
            "field": "rol_target_pct",
            "displayFormat": {"category": "percent", "decimalPlaces": 1},
        },
    }
    out = DisplayFormatService.apply_to_resolved(resolved, block)
    assert out["serverDisplayApplied"] is True
    assert out["displayText"] == "41,7%"
    assert out["displayRuns"] == [{"text": "41,7%"}]


def test_apply_to_resolved_text_from_metric_field_value_dump():
    """FE-BE-003: metric/field/value table must still resolve textProjection.field."""
    resolved = {
        "kpi": {"value": 12, "label": "Ganhos"},
        "kpiMetrics": [
            {"field": "gains", "label": "Ganhos", "value": 12},
            {"field": "goal_value", "label": "Meta", "value": 10},
        ],
        "table": {
            "columns": [
                {"key": "metric", "label": "Indicador"},
                {"key": "field", "label": "Campo"},
                {"key": "value", "label": "Valor"},
            ],
            "rows": [
                {"metric": "Ganhos", "field": "gains", "value": 12},
                {"metric": "Meta", "field": "goal_value", "value": 10},
            ],
        },
    }
    block = {
        "type": "text",
        "dataSourceId": "src-1",
        "textProjection": {
            "field": "gains",
            "prefix": "Ganhos ",
            "suffix": " este mês",
            "displayFormat": {"category": "number", "decimalPlaces": 0},
        },
    }
    out = DisplayFormatService.apply_to_resolved(resolved, block)
    assert out["displayText"] == "Ganhos 12 este mês"
    assert out["serverDisplayApplied"] is True


def test_apply_to_resolved_content_runs_win_over_projection():
    resolved = {
        "contextValues": {
            "filter.start_date": "2026-01-01",
            "filter.end_date": "2026-09-24",
        },
        "kpi": {"value": 99, "label": "Rol"},
        "kpiMetrics": [{"field": "Rol", "value": 99}],
    }
    block = {
        "type": "text",
        "dataSourceId": "src-1",
        "textProjection": {"field": "Rol", "format": "number"},
        "contentRuns": [
            {"text": "ACUMULADO "},
            {
                "dataRef": {
                    "field": "filter.start_date",
                    "displayFormat": {
                        "category": "date",
                        "presetId": "date-short",
                    },
                }
            },
            {"text": " - "},
            {
                "dataRef": {
                    "field": "filter.end_date",
                    "displayFormat": {
                        "category": "date",
                        "presetId": "date-short",
                    },
                }
            },
        ],
    }
    out = DisplayFormatService.apply_to_resolved(resolved, block)
    assert out["displayText"] == "ACUMULADO 01/01/2026 - 24/09/2026"
    assert out["serverDisplayApplied"] is True


def test_apply_to_resolved_kpi_display_value():
    resolved = {"kpi": {"value": 10.5, "label": "X"}, "kpiMetrics": []}
    block = {
        "type": "kpi_view",
        "kpiOptions": {
            "valueFormat": "currency",
            "displayValueFormat": {
                "category": "currency",
                "currency": "BRL",
                "decimalPlaces": 2,
            },
        },
    }
    out = DisplayFormatService.apply_to_resolved(resolved, block)
    assert "10,50" in out["kpi"]["displayValue"]
    assert out["serverDisplayApplied"] is True


def test_apply_to_resolved_chart_labels_when_specs_exist():
    resolved = {
        "chart": {
            "chartType": "line",
            "points": [
                {"label": "2026-08-03", "value": 41.7},
                {"label": "Jan. de 26", "value": 10},
            ],
        }
    }
    block = {
        "type": "chart_view",
        "chartOptions": {
            "categoryLabelFormat": "day",
            "valueFormat": "percent",
            "decimalPlaces": 1,
        },
    }
    out = DisplayFormatService.apply_to_resolved(resolved, block)
    points = out["chart"]["points"]
    assert points[0]["displayLabel"] == "03/08/2026"
    assert points[0]["displayValue"] == "41,7%"
    assert points[1]["displayLabel"] == "Jan. de 26"
    assert isinstance(out["chart"].get("yAxisTicks"), list)
    assert len(out["chart"]["yAxisTicks"]) >= 2
    assert "displayLabel" in out["chart"]["yAxisTicks"][0]


def test_apply_to_resolved_chart_axis_ticks_without_value_spec():
    resolved = {
        "chart": {
            "chartType": "bar",
            "points": [
                {"label": "a", "value": 10},
                {"label": "b", "value": 90},
            ],
        }
    }
    out = DisplayFormatService.apply_to_resolved(resolved, {"type": "chart_view"})
    ticks = out["chart"]["yAxisTicks"]
    assert len(ticks) >= 2
    assert all("displayLabel" in t and "value" in t for t in ticks)
    assert out["serverDisplayApplied"] is True


def test_sanitize_contradictory_text_binding_clears_data_refs():
    """Campo-equivalent write: keep textProjection, strip dataRefs (static runs stay)."""
    block = {
        "type": "text",
        "textProjection": {"field": "Rol", "format": "number"},
        "contentRuns": [
            {"text": "ACUMULADO "},
            {"dataRef": {"field": "filter.start_date"}},
            {"text": " - "},
            {"dataRef": {"field": "filter.end_date"}},
        ],
    }
    sanitized = DisplayFormatService.sanitize_contradictory_text_binding(block)
    assert sanitized["textProjection"]["field"] == "Rol"
    assert sanitized["contentRuns"] == [{"text": "ACUMULADO "}, {"text": " - "}]


def test_sanitize_compatible_single_data_ref_still_consolidates():
    block = {
        "type": "text",
        "textProjection": {"field": "oee"},
        "contentRuns": [{"dataRef": {"field": "oee"}}],
    }
    sanitized = DisplayFormatService.sanitize_contradictory_text_binding(block)
    assert sanitized["textProjection"]["field"] == "oee"
    assert "contentRuns" not in sanitized


def test_apply_to_resolved_date_short_is_dd_mm_yyyy_not_iso():
    resolved = {
        "contextValues": {"filter.start_date": "2026-08-03"},
    }
    block = {
        "type": "text",
        "dataSourceId": "src-1",
        "textProjection": {
            "field": "filter.start_date",
            "displayFormat": {"category": "date", "presetId": "date-short"},
        },
    }
    out = DisplayFormatService.apply_to_resolved(resolved, block)
    assert out["serverDisplayApplied"] is True
    assert out["displayText"] == "03/08/2026"
    assert "2026-08-03" not in out["displayText"]
    signals = DisplayFormatService.display_signals_for_verify(out)
    assert signals["serverDisplayApplied"] is True
    assert signals["displayText"] == "03/08/2026"


def test_apply_canvas_table_source_map_materializes_display_runs():
    """G16: células com dataRef recebem displayRuns no resolved da fonte."""
    by_source = {
        "src-1": {
            "kpi": {"value": 41.7},
            "kpiMetrics": [{"field": "oee", "value": 41.7}],
            "fields": [{"name": "oee", "projectable": True}],
        }
    }
    block = {
        "type": "canvas_table",
        "dataSourceId": "src-1",
        "cells": [
            [
                {
                    "dataRef": {
                        "field": "oee",
                        "displayFormat": {"category": "percent", "decimalPlaces": 1},
                    }
                }
            ]
        ],
    }
    out = DisplayFormatService.apply_canvas_table_source_map(block, by_source)
    assert out["src-1"]["serverDisplayApplied"] is True
    assert out["src-1"]["displayRuns"]
    assert out["src-1"]["displayRuns"][0]["text"] == "41,7%"
