"""FORMAT-001 — server-owned format catalog + batch previews + date expansion."""

from __future__ import annotations

from tv_app.application.services.data.display_format_service import DisplayFormatService


def test_date_format_matrix_2026_09_24():
    value = "2026-09-24"
    expected = {
        "date-short": "24/09/2026",
        "date-short-yy": "24/09/26",
        "date-month-year": "09/2026",
        "date-month-year-yy": "09/26",
        "date-month-year-dash": "09-2026",
        "date-month-year-dash-yy": "09-26",
        "date-year-month": "2026/09",
        "date-year-month-yy": "26/09",
        "date-iso": "2026-09-24",
        "date-year": "2026",
        "date-year-yy": "26",
        "date-month-abbrev-year": "set./2026",
        "date-month-abbrev-year-yy": "set./26",
        "date-month-full-year": "setembro/2026",
        "date-month-full-year-yy": "setembro/26",
        "date-month-abbrev-de-year": "set de 2026",
        "date-month-full-de-year": "setembro de 2026",
        "date-day-mon-year": "24 set. 2026",
        "date-day-mon-year-yy": "24 set. 26",
        "date-day-full-long": "24 de setembro de 2026",
        "date-day-full-long-yy": "24 de setembro de 26",
        "date-month-num": "09",
        "date-month-abbrev": "set.",
        "date-month-full": "setembro",
    }
    for format_id, want in expected.items():
        result = DisplayFormatService.try_format_value(
            value, DisplayFormatService.spec_from_preset_id(format_id)
        )
        assert result["convertible"] is True, format_id
        assert result["preview"] == want, (format_id, result["preview"], want)


def test_date_only_does_not_shift_calendar_day():
    """DATE (no time) must not become previous day via TZ conversion."""
    assert (
        DisplayFormatService.format_value(
            "2026-09-24", DisplayFormatService.spec_from_preset_id("date-short")
        )
        == "24/09/2026"
    )
    assert (
        DisplayFormatService.format_value(
            "2026-09-24T00:00:00",
            DisplayFormatService.spec_from_preset_id("date-short"),
        )
        == "24/09/2026"
    )


def test_non_convertible_invalid_string_is_explicit():
    result = DisplayFormatService.try_format_value(
        "ABC", DisplayFormatService.spec_from_preset_id("date-month-year")
    )
    assert result["convertible"] is False
    assert result["preview"] is None
    assert result["reasonCode"] in {"PARSE_FAILED", "VALUE_NOT_DATE", "VALUE_INVALID"}
    assert result["reason"]


def test_null_empty_missing_distinct():
    null_r = DisplayFormatService.try_format_value(
        None, DisplayFormatService.spec_from_preset_id("date-short")
    )
    empty_r = DisplayFormatService.try_format_value(
        "", DisplayFormatService.spec_from_preset_id("date-short")
    )
    assert null_r["reasonCode"] == "VALUE_NULL"
    assert empty_r["reasonCode"] == "VALUE_EMPTY"
    assert null_r["preview"] is None
    assert empty_r["preview"] is None


def test_preview_catalog_batch_one_shot():
    payload = DisplayFormatService.preview_format_catalog(
        value="2025-09-24",
        semantic_type="date",
        value_source="authoritative",
    )
    assert payload["valueSource"] == "authoritative"
    assert len(payload["options"]) >= 20
    by_id = {item["formatId"]: item for item in payload["options"]}
    assert by_id["date-month-year"]["preview"] == "09/2025"
    assert by_id["date-month-year-yy"]["preview"] == "09/25"
    assert by_id["date-short"]["preview"] == "24/09/2025"
    assert by_id["date-month-abbrev-year"]["preview"] == "set./2025"
    assert by_id["date-month-full-year"]["preview"] == "setembro/2025"
    assert by_id["date-iso"]["preview"] == "2025-09-24"
    assert by_id["date-year"]["preview"] == "2025"
    # custom included separately
    assert payload["custom"]["formatId"] == "custom"


def test_preview_equals_final_display_invariant():
    value = "2026-09-24"
    for format_id in (
        "date-short",
        "date-month-year",
        "date-month-abbrev-year",
        "date-day-full-long",
        "date-iso",
        "number-2",
        "currency-brl",
        "percent",
    ):
        spec = DisplayFormatService.spec_from_preset_id(format_id)
        preview = DisplayFormatService.try_format_value(value if format_id.startswith("date") else 1234.56, spec)
        if not preview["convertible"]:
            continue
        final = DisplayFormatService.format_value(
            value if format_id.startswith("date") else 1234.56, spec
        )
        assert preview["preview"] == final, format_id


def test_legacy_date_presets_remain():
    for format_id in (
        "date-short",
        "date-long",
        "date-iso",
        "date-day-mon",
        "date-month",
        "date-year",
        "date-auto",
    ):
        assert format_id in {
            e["formatId"] for e in DisplayFormatService.format_catalog_entries()
        }
        assert DisplayFormatService.spec_from_preset_id(format_id)["category"] == "date"


def test_mm_yyyy_and_mm_yy_available():
    ids = {e["formatId"] for e in DisplayFormatService.format_catalog_entries()}
    assert "date-month-year" in ids
    assert "date-month-year-yy" in ids
