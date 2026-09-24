"""G10/G11/G25–G28 — presentation materialization on enrich."""

from tv_app.application.services.data.display_format_service import DisplayFormatService


def test_kpi_presentation_auto_sparkline():
    resolved = {
        "kpi": {"value": 100, "label": "OEE"},
        "chart": {
            "points": [
                {"label": "a", "value": 80},
                {"label": "b", "value": 90},
                {"label": "c", "value": 100},
            ]
        },
    }
    block = {
        "type": "kpi_view",
        "kpiOptions": {
            "contextMode": "auto",
            "valueFormat": "number",
            "decimalPlaces": 0,
        },
    }
    out = DisplayFormatService.apply_to_resolved(resolved, block)
    pres = out["kpiPresentation"]
    assert pres["valueDisplay"]
    assert isinstance(pres["sparklinePoints"], list)
    assert len(pres["sparklinePoints"]) == 3
    assert pres["comparisonDisplay"]
    assert "yAxisTicks" not in out  # kpi path


def test_chart_effective_goal_and_ticks_include_meta():
    resolved = {
        "chart": {
            "chartType": "line",
            "projectedGoal": 95,
            "points": [
                {"label": "a", "value": 10},
                {"label": "b", "value": 40},
            ],
        }
    }
    block = {"type": "chart_view", "chartOptions": {}}
    out = DisplayFormatService.apply_to_resolved(resolved, block)
    assert out["chart"]["effectiveGoal"] == 95.0
    ticks = out["chart"]["yAxisTicks"]
    assert len(ticks) >= 2
    assert max(t["value"] for t in ticks) >= 95


def test_gauge_model_materialized():
    resolved = {
        "kpi": {"value": 87.5, "label": "Eficiência"},
        "chart": {"chartType": "gauge", "projectedGoal": 95, "points": []},
    }
    block = {
        "type": "chart_view",
        "chartType": "gauge",
        "chartOptions": {"title": "CT"},
    }
    out = DisplayFormatService.apply_to_resolved(resolved, block)
    model = out["chart"]["gaugeModel"]
    assert model["value"] == 87.5
    assert model["goal"] == 95.0
    assert model["valueDisplay"]
    assert model["goalDisplay"]


def test_efficiency_pin_presentation():
    resolved = {
        "table": {
            "rows": [
                {"work_center": "CT-01", "efficiency_pct": 96.5, "appointment_count": 3},
            ],
            "columns": [{"key": "work_center"}, {"key": "efficiency_pct"}],
        }
    }
    block = {
        "type": "shape",
        "efficiencyPin": {
            "workCenter": "CT-01",
            "bands": {"goodMinPct": 95, "warnMinPct": 50, "validMaxPct": 199},
        },
    }
    out = DisplayFormatService.apply_to_resolved(resolved, block)
    pin = out["efficiencyPinPresentation"]
    assert pin["status"] == "good"
    assert pin["efficiencyPct"] == 96.5
    assert "%" in pin["efficiencyPctDisplay"] or "96" in pin["efficiencyPctDisplay"]
    signals = DisplayFormatService.display_signals_for_verify(out)
    assert "efficiencyPinPresentation" in signals


def test_canvas_display_series():
    by_source = {
        "src-1": {
            "table": {
                "rows": [
                    {"oee": 10},
                    {"oee": 20},
                    {"oee": 30},
                ],
                "columns": [{"key": "oee"}],
            },
            "fields": [{"name": "oee", "projectable": True}],
        }
    }
    block = {
        "type": "canvas_table",
        "dataSourceId": "src-1",
        "cells": [[{"dataRef": {"field": "oee", "aggregation": "list"}}]],
    }
    out = DisplayFormatService.apply_canvas_table_source_map(block, by_source)
    series = out["src-1"].get("displaySeries") or {}
    assert "oee" in series
    assert series["oee"] == [10.0, 20.0, 30.0]
