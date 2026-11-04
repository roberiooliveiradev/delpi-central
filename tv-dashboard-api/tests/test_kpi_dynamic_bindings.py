"""VISTA-TV-DYNAMIC-BINDINGS-001 — matriz A–J (unit/contract)."""

from __future__ import annotations

from tv_app.application.services.data.display_format_service import DisplayFormatService


def _table_resolved(*, realizado: float | None, meta: float | None, titulo="OEE", sub="Turno A"):
    row = {"titulo": titulo, "subtitulo": sub}
    if realizado is not None:
        row["realizado"] = realizado
    if meta is not None:
        row["meta"] = meta
    return {
        "kpi": {"value": realizado, "displayValue": str(realizado) if realizado is not None else "—"},
        "table": {
            "columns": [
                {"key": "realizado"},
                {"key": "meta"},
                {"key": "titulo"},
                {"key": "subtitulo"},
            ],
            "rows": [row],
        },
    }


def test_a_principal_value_meta_title_subtitle_comparison_and_color():
    """A — um DataModel alimenta valor, meta, títulos e cor."""
    resolved = _table_resolved(realizado=90.0, meta=85.0)
    block = {
        "kpiOptions": {
            "contextMode": "auto",
            "comparisonMode": "target",
            "showComparison": True,
            "showProgress": True,
            "titleField": "titulo",
            "subtitleField": "subtitulo",
            "colorRules": [{"op": "gte", "compareField": "meta", "tone": "positive"}],
            "higherIsBetter": True,
        },
        "kpiProjection": {
            "metrics": [
                {
                    "field": "realizado",
                    "targetField": "meta",
                    "targetAggregation": "first",
                    "comparisonMode": "target",
                }
            ]
        },
    }
    DisplayFormatService._apply_kpi_presentation(resolved, block)
    pres = resolved["kpiPresentation"]
    assert pres["targetValue"] == 85.0
    assert pres["titleDisplay"] == "OEE"
    assert pres["subtitleDisplay"] == "Turno A"
    assert pres["progressPct"] is not None
    assert "vs meta" in (pres["comparisonDisplay"] or "")
    assert pres["comparisonTone"] == "positive"
    assert pres["resolvedColorRules"]
    assert pres["resolvedColorRules"][0]["value"] == 85.0
    assert "compareField" not in pres["resolvedColorRules"][0]


def test_b_meta_changes_without_reediting_slide():
    """B — mesma config; meta nova no dado → comparação/progresso mudam."""
    block = {
        "kpiOptions": {
            "contextMode": "manual",
            "comparisonMode": "target",
            "showComparison": True,
            "showProgress": True,
            "higherIsBetter": True,
        },
        "kpiProjection": {
            "metrics": [{"field": "realizado", "targetField": "meta", "comparisonMode": "target"}]
        },
    }
    first = _table_resolved(realizado=90.0, meta=100.0)
    DisplayFormatService._apply_kpi_presentation(first, block)
    assert first["kpiPresentation"]["targetValue"] == 100.0
    assert first["kpiPresentation"]["statusLabel"] == "Abaixo da meta"
    assert first["kpiPresentation"]["comparisonTone"] == "negative"

    second = _table_resolved(realizado=90.0, meta=80.0)
    DisplayFormatService._apply_kpi_presentation(second, block)
    assert second["kpiPresentation"]["targetValue"] == 80.0
    assert second["kpiPresentation"]["statusLabel"] == "Acima da meta"
    assert second["kpiPresentation"]["comparisonTone"] == "positive"
    assert second["kpiPresentation"]["progressPct"] == 112.5


def test_c_higher_is_better_oee_below_equal_above():
    """C — maior é melhor (OEE)."""
    block = {
        "kpiOptions": {
            "contextMode": "manual",
            "comparisonMode": "target",
            "showComparison": True,
            "higherIsBetter": True,
        },
        "kpiProjection": {
            "metrics": [{"field": "realizado", "targetField": "meta", "comparisonMode": "target"}]
        },
    }
    for value, expect_tone, expect_status in (
        (80.0, "negative", "Abaixo da meta"),
        (85.0, "neutral", "Na meta"),
        (90.0, "positive", "Acima da meta"),
    ):
        resolved = _table_resolved(realizado=value, meta=85.0)
        DisplayFormatService._apply_kpi_presentation(resolved, block)
        assert resolved["kpiPresentation"]["comparisonTone"] == expect_tone
        assert resolved["kpiPresentation"]["statusLabel"] == expect_status


def test_d_lower_is_better_rework():
    """D — menor é melhor (retrabalho): abaixo da meta é positivo."""
    block = {
        "kpiOptions": {
            "contextMode": "manual",
            "comparisonMode": "target",
            "showComparison": True,
            "higherIsBetter": False,
        },
        "kpiProjection": {
            "metrics": [
                {
                    "field": "realizado",
                    "targetField": "meta",
                    "comparisonMode": "target",
                    "higherIsBetter": False,
                }
            ]
        },
    }
    below = _table_resolved(realizado=3.0, meta=5.0)
    DisplayFormatService._apply_kpi_presentation(below, block)
    assert below["kpiPresentation"]["comparisonTone"] == "positive"
    assert below["kpiPresentation"]["statusLabel"] == "Abaixo da meta"

    above = _table_resolved(realizado=8.0, meta=5.0)
    DisplayFormatService._apply_kpi_presentation(above, block)
    assert above["kpiPresentation"]["comparisonTone"] == "negative"


def test_e_invalid_missing_and_zero_meta():
    """E — campo ausente, null e meta 0 (sem progresso)."""
    block = {
        "kpiOptions": {
            "contextMode": "manual",
            "comparisonMode": "target",
            "showComparison": True,
            "showProgress": True,
            "titleField": "missing_title",
        },
        "kpiProjection": {
            "metrics": [
                {"field": "realizado", "targetField": "missing_meta", "comparisonMode": "target"}
            ]
        },
    }
    resolved = _table_resolved(realizado=10.0, meta=None)
    # drop meta column entirely for missing field
    resolved["table"]["rows"][0].pop("meta", None)
    DisplayFormatService._apply_kpi_presentation(resolved, block)
    pres = resolved["kpiPresentation"]
    assert pres["targetValue"] is None
    assert pres["progressPct"] is None
    codes = {d["code"] for d in (pres["bindingDiagnostics"] or [])}
    assert "kpi_target_field_unresolved" in codes
    assert "kpi_title_field_unresolved" in codes

    zero_meta = _table_resolved(realizado=10.0, meta=0.0)
    block_zero = {
        "kpiOptions": {
            "contextMode": "manual",
            "comparisonMode": "target",
            "showComparison": True,
            "showProgress": True,
        },
        "kpiProjection": {
            "metrics": [{"field": "realizado", "targetField": "meta", "comparisonMode": "target"}]
        },
    }
    DisplayFormatService._apply_kpi_presentation(zero_meta, block_zero)
    # zero é meta válida, mas progresso evita divisão por zero
    assert zero_meta["kpiPresentation"]["targetValue"] == 0.0
    assert zero_meta["kpiPresentation"]["progressPct"] is None


def test_f_literal_meta_compatibility():
    """F — slides legados com meta literal intactos."""
    resolved = {"kpi": {"value": 110.0, "displayValue": "110"}}
    block = {
        "kpiOptions": {
            "contextMode": "manual",
            "comparisonMode": "target",
            "showComparison": True,
            "showProgress": True,
            "target": 100.0,
            "higherIsBetter": True,
            "colorRules": [{"op": "gte", "value": 100, "tone": "positive"}],
        },
        "kpiProjection": {"metrics": [{"field": "x", "target": 100.0, "format": "number"}]},
    }
    DisplayFormatService._apply_kpi_presentation(resolved, block)
    pres = resolved["kpiPresentation"]
    assert pres["targetValue"] == 100.0
    assert "+10" in (pres["comparisonDisplay"] or "")
    assert pres["resolvedColorRules"][0]["value"] == 100


def test_target_field_wins_over_literal():
    resolved = _table_resolved(realizado=50.0, meta=40.0)
    block = {
        "kpiOptions": {
            "contextMode": "manual",
            "comparisonMode": "target",
            "showComparison": True,
            "target": 999.0,
        },
        "kpiProjection": {
            "metrics": [{"field": "realizado", "targetField": "meta", "target": 999.0}]
        },
    }
    DisplayFormatService._apply_kpi_presentation(resolved, block)
    assert resolved["kpiPresentation"]["targetValue"] == 40.0


def test_compare_field_unresolved_skips_rule_with_diagnostic():
    resolved = _table_resolved(realizado=50.0, meta=40.0)
    block = {
        "kpiOptions": {
            "colorRules": [
                {"op": "gte", "compareField": "nope", "tone": "positive"},
                {"op": "gte", "value": 10, "tone": "warning"},
            ],
        },
        "kpiProjection": {"metrics": [{"field": "realizado"}]},
    }
    DisplayFormatService._apply_kpi_presentation(resolved, block)
    rules = resolved["kpiPresentation"]["resolvedColorRules"]
    assert len(rules) == 1
    assert rules[0]["tone"] == "warning"
    assert any(
        d["code"] == "kpi_color_compare_field_unresolved"
        for d in (resolved["kpiPresentation"]["bindingDiagnostics"] or [])
    )
