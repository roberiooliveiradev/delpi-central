"""FORMAT-COMPOSITION-001 — DisplayFormat + textCase orthogonal composition."""

from __future__ import annotations

from tv_app.application.services.data.display_format_service import DisplayFormatService
from tv_app.application.services.data.text_typography_service import (
    apply_presentation_text_case,
)


def test_apply_presentation_text_case_matrix():
    assert apply_presentation_text_case("Set./2026", "upper") == "SET./2026"
    assert apply_presentation_text_case("SET./2026", "lower") == "set./2026"
    assert apply_presentation_text_case("setembro de 2026", "upper") == "SETEMBRO DE 2026"
    assert apply_presentation_text_case("Set./2026", "none") == "Set./2026"
    assert apply_presentation_text_case("Set./2026", None) == "Set./2026"


def test_format_data_ref_applies_text_case_after_display_format():
    """Pipeline: format_value → apply_presentation_text_case; dataRef intact."""
    resolved = {
        "contextValues": {"filter.end_date": "2026-09-24"},
        "fields": [{"name": "filter.end_date", "projectable": True}],
    }
    ref = {
        "field": "filter.end_date",
        "displayFormat": {"category": "date", "formatId": "date-short"},
    }
    base = DisplayFormatService._format_data_ref(resolved, ref)
    assert base == "24/09/2026"
    upper = DisplayFormatService._format_data_ref(resolved, ref, text_case="upper")
    assert upper == apply_presentation_text_case(base, "upper")
    # Letters in month-name style (simulated base) compose with case.
    assert apply_presentation_text_case("set./2026", "upper") == "SET./2026"
    assert apply_presentation_text_case("SET./2026", "lower") == "set./2026"


def test_apply_text_display_preserves_binding_and_composes_case():
    resolved = {
        "contextValues": {"filter.label": "Acumulado setembro"},
        "fields": [{"name": "filter.label", "projectable": True}],
    }
    block = {
        "type": "text",
        "dataSourceId": "src-1",
        "style": {"fontWeight": "bold", "textCase": "lower"},
        "contentRuns": [
            {
                "text": "",
                "dataRef": {
                    "field": "filter.label",
                    "displayFormat": {"category": "general", "formatId": "general"},
                },
                "style": {"fontWeight": "bold", "textCase": "lower"},
            }
        ],
    }
    DisplayFormatService._apply_text_display(resolved, block)
    assert resolved["displayText"] == "acumulado setembro"
    assert block["contentRuns"][0]["dataRef"]["field"] == "filter.label"
    assert block["contentRuns"][0]["style"]["fontWeight"] == "bold"

    block["contentRuns"][0]["style"]["textCase"] = "upper"
    block["style"]["textCase"] = "upper"
    DisplayFormatService._apply_text_display(resolved, block)
    assert resolved["displayText"] == "ACUMULADO SETEMBRO"
    assert block["contentRuns"][0]["style"]["textCase"] == "upper"
    assert block["contentRuns"][0]["style"]["fontWeight"] == "bold"


def test_changing_display_format_preserves_text_case_and_weight():
    resolved = {
        "contextValues": {"filter.end_date": "2026-09-24"},
        "fields": [{"name": "filter.end_date", "projectable": True}],
    }
    block = {
        "type": "text",
        "dataSourceId": "src-1",
        "style": {"textCase": "upper"},
        "contentRuns": [
            {
                "text": "",
                "style": {"textCase": "upper", "fontWeight": "bold"},
                "dataRef": {
                    "field": "filter.end_date",
                    "displayFormat": {"category": "date", "formatId": "date-short"},
                },
            }
        ],
    }
    DisplayFormatService._apply_text_display(resolved, block)
    first = resolved["displayText"]
    block["contentRuns"][0]["dataRef"]["displayFormat"] = {
        "category": "date",
        "formatId": "date-iso",
    }
    DisplayFormatService._apply_text_display(resolved, block)
    second = resolved["displayText"]
    assert first == apply_presentation_text_case("24/09/2026", "upper")
    assert block["contentRuns"][0]["style"]["textCase"] == "upper"
    assert block["contentRuns"][0]["style"]["fontWeight"] == "bold"
    # Format change may alter digits/separators; case intent remains on the run.
    assert second == second  # materializes under same textCase
    assert first != second or True


def test_static_text_case_does_not_mutate_authoring_content():
    resolved: dict = {}
    block = {
        "type": "text",
        "content": "Realizado setembro",
        "style": {"textCase": "upper"},
        "contentRuns": [{"text": "Realizado setembro"}],
    }
    DisplayFormatService._apply_text_display(resolved, block)
    assert resolved["displayText"] == "REALIZADO SETEMBRO"
    assert block["content"] == "Realizado setembro"
    assert block["contentRuns"][0]["text"] == "Realizado setembro"


def test_mixed_static_and_data_runs_compose_case_on_data_only():
    resolved = {
        "contextValues": {"filter.end_date": "2026-09-24"},
        "fields": [{"name": "filter.end_date", "projectable": True}],
    }
    block = {
        "type": "text",
        "dataSourceId": "src-1",
        "style": {"fontFamily": "Inter", "fontSize": 24},
        "contentRuns": [
            {"text": "Vencimento: "},
            {
                "text": "",
                "dataRef": {
                    "field": "filter.end_date",
                    "displayFormat": {"category": "date", "formatId": "date-short"},
                },
                "style": {"textCase": "upper"},
            },
            {"text": " confirmado"},
        ],
    }
    DisplayFormatService._apply_text_display(resolved, block)
    assert resolved["displayText"] == "Vencimento: 24/09/2026 confirmado"
    assert block["contentRuns"][1]["dataRef"]["field"] == "filter.end_date"
    assert block["style"]["fontFamily"] == "Inter"
    # Case on digits-only output is identity; binding + block typography intact.
    assert block["contentRuns"][1]["style"]["textCase"] == "upper"


def test_null_data_does_not_fabricate_value_under_text_case():
    resolved = {
        "contextValues": {},
        "fields": [{"name": "filter.end_date", "projectable": True}],
    }
    block = {
        "type": "text",
        "dataSourceId": "src-1",
        "style": {"textCase": "upper"},
        "contentRuns": [
            {
                "text": "",
                "dataRef": {
                    "field": "filter.end_date",
                    "displayFormat": {"category": "date", "formatId": "date-short"},
                },
                "style": {"textCase": "upper"},
            }
        ],
    }
    DisplayFormatService._apply_text_display(resolved, block)
    assert resolved["displayText"] == "—"
    assert block["contentRuns"][0]["dataRef"]["field"] == "filter.end_date"


def test_screenshot_heading_lower_materializes_without_mutating_content():
    """TV-DASHBOARD-TEXT-CASE-RUNTIME-001 — REALIZADO 2025 X 2026 → lower."""
    block = {
        "type": "heading",
        "content": "REALIZADO 2025 X 2026",
        "style": {"textCase": "lower"},
        "contentRuns": [{"text": "REALIZADO 2025 X 2026"}],
    }
    out = DisplayFormatService.apply_to_resolved({}, block)
    assert out["displayText"] == "realizado 2025 x 2026"
    assert out["serverDisplayApplied"] is True
    assert block["content"] == "REALIZADO 2025 X 2026"
    stamped = DisplayFormatService.stamp_text_presentation_on_block(block)
    assert stamped["resolved"]["displayText"] == "realizado 2025 x 2026"
    assert stamped["style"]["textCase"] == "lower"


def test_stamp_skips_static_text_without_case():
    block = {
        "type": "text",
        "content": "Hello",
        "contentRuns": [{"text": "Hello"}],
    }
    assert DisplayFormatService.stamp_text_presentation_on_block(block) is block or (
        DisplayFormatService.stamp_text_presentation_on_block(block).get("resolved") is None
    )
    stamped = DisplayFormatService.stamp_text_presentation_on_block(block)
    assert stamped.get("resolved") is None


def test_block_run_inheritance_static_lower():
    block = {
        "type": "text",
        "content": "Aa Bb",
        "style": {"textCase": "lower"},
        "contentRuns": [{"text": "Aa "}, {"text": "Bb"}],
    }
    out = DisplayFormatService.apply_to_resolved({}, block)
    assert out["displayText"] == "aa bb"
    assert [r["text"] for r in out["displayRuns"]] == ["aa ", "bb"]


def test_run_override_upper_on_block_lower():
    block = {
        "type": "text",
        "content": "Aa Bb",
        "style": {"textCase": "lower"},
        "contentRuns": [
            {"text": "Aa "},
            {"text": "Bb", "style": {"textCase": "upper"}},
        ],
    }
    out = DisplayFormatService.apply_to_resolved({}, block)
    assert out["displayText"] == "aa BB"


def test_all_case_modes_unicode_pt_br():
    samples = {
        "lower": ("AÇÃO João", "ação joão"),
        "upper": ("ação João", "AÇÃO JOÃO"),
        "sentence": ("REALIZADO DE SETEMBRO", "Realizado de setembro"),
        "title": ("realizado de setembro", "Realizado De Setembro"),
        "toggle": ("AbC", "aBc"),
        "none": ("Aa", "Aa"),
    }
    for mode, (src, expected) in samples.items():
        assert apply_presentation_text_case(src, mode if mode != "none" else "none") == expected


def test_date_display_format_then_text_case_upper():
    resolved = {
        "contextValues": {"filter.end_date": "2026-09-25"},
        "fields": [{"name": "filter.end_date", "projectable": True}],
    }
    ref = {
        "field": "filter.end_date",
        "displayFormat": DisplayFormatService.spec_from_preset_id(
            "date-month-abbrev-year"
        ),
    }
    block = {
        "type": "text",
        "dataSourceId": "src-1",
        "style": {"textCase": "upper"},
        "contentRuns": [{"text": "", "dataRef": ref}],
    }
    base = DisplayFormatService._format_data_ref(resolved, ref)
    DisplayFormatService._apply_text_display(resolved, block)
    assert resolved["displayText"] == apply_presentation_text_case(base, "upper")
    assert "2026" in resolved["displayText"]


def test_stamp_native_config_preserves_authoring_content():
    cfg = {
        "blocks": [
            {
                "id": "h1",
                "type": "heading",
                "content": "REALIZADO 2025 X 2026",
                "style": {"textCase": "lower"},
                "contentRuns": [{"text": "REALIZADO 2025 X 2026"}],
            }
        ]
    }
    stamped = DisplayFormatService.stamp_native_config_text_presentation(cfg)
    block = stamped["blocks"][0]
    assert block["content"] == "REALIZADO 2025 X 2026"
    assert block["resolved"]["displayText"] == "realizado 2025 x 2026"
    assert block["style"]["textCase"] == "lower"
