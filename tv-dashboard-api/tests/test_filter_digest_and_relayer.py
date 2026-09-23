"""Filter digest + re_layer_playlist_filters."""

from __future__ import annotations

from tv_app.application.services.data.filter_digest_service import FilterDigestService
from tv_app.application.services.data.filter_relayer_service import apply_relayer
from tv_app.application.services.data.ready_slide_quality_service import ReadySlideQualityService


def _native_with_sources(*params_list: dict) -> dict:
    blocks = []
    for index, params in enumerate(params_list):
        blocks.append(
            {
                "id": f"ds-{index}",
                "type": "data_source",
                "dataBinding": {
                    "operationId": "get_on_time_delivery_pct",
                    "params": dict(params),
                },
            }
        )
    return {"version": 5, "blocks": blocks}


def test_filter_digest_detects_duplicates_and_wrong_layer():
    native = _native_with_sources(
        {"branch": "01", "dateRangePreset": "this_month"},
        {"branch": "01", "dateRangePreset": "this_month"},
    )
    digest = FilterDigestService.digest_slide(native, slide_id="s1")
    assert digest["duplicates"]
    assert any("shared_" in hint for hint in digest["wrongLayerHints"])


def test_relayer_promotes_to_slide_data_filters():
    native = _native_with_sources(
        {"branch": "01", "dateRangePreset": "this_month"},
        {"branch": "01", "dateRangePreset": "this_month"},
    )
    apply_relayer(native, scope="slide", keys=None, playlist_defaults={})
    assert native.get("dataFilters", {}).get("branch") == "01"
    params = native["blocks"][0]["dataBinding"]["params"]
    assert "branch" not in params
    assert "dateRangePreset" not in params


def test_enrich_skips_period_when_playlist_defaults_have_preset():
    route = {
        "paramStrategy": "date_range",
        "openEndedDateRange": False,
        "paramSchema": {"dateRangePreset": {"optional": False}},
    }
    out = ReadySlideQualityService.enrich_data_source_params(
        route,
        {},
        playlist_defaults={"dateRangePreset": "this_week"},
    )
    assert "dateRangePreset" not in out


def test_quality_merge_uses_playlist_defaults_for_period_check():
    native = _native_with_sources({})
    native["dataFilters"] = {}
    route = {
        "paramStrategy": "date_range",
        "openEndedDateRange": False,
        "paramSchema": {"dateRangePreset": {"optional": False}},
    }

    class _Cat:
        def get_route(self, _op: str):
            return route

    issues = ReadySlideQualityService.collect_native_quality_issues(
        native,
        catalog=_Cat(),
        playlist_defaults={"dateRangePreset": "this_month"},
    )
    assert not any(i.startswith("params.incomplete") for i in issues)
