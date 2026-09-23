"""Corpus gate — structural markers must exist in JSON SoT + unit smoke."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tv_app.application.gpt_actions.vista_agent_intelligence_service import (
    VistaAgentIntelligenceService,
    clear_vista_agent_intelligence_cache,
)
from tv_app.application.services.data.filter_digest_service import FilterDigestService
from tv_app.application.services.data.filter_relayer_service import apply_relayer
from tv_app.application.services.data.presentation_ops_content_service import (
    PresentationOpsContentService,
)
from tv_app.application.services.data.presentation_recipe_service import (
    PresentationRecipeService,
    clear_presentation_recipes_cache,
)
from tv_app.application.services.data.ready_slide_quality_service import (
    ReadySlideQualityService,
)
from tv_app.application.services.editor_focus_store import EditorFocusStore
from tv_app.application.services.slide_template_mdd_service import SLIDE_TEMPLATES_DIR

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "vista_ready_slide_corpus.json"


def setup_function() -> None:
    clear_vista_agent_intelligence_cache()
    clear_presentation_recipes_cache()


def teardown_function() -> None:
    clear_vista_agent_intelligence_cache()
    clear_presentation_recipes_cache()


def _corpus() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_corpus_fixture_cases_present():
    data = _corpus()
    cases = data.get("cases") or {}
    required = [f"C{i}" for i in range(15, 32)] + [
        "G_LOGO_THEME",
        "G_AUTO_LAYOUT",
        "G_BLANK_SLIDE",
        "G_TEMPLATE",
        "G_EDITOR_FOCUS",
        "G_MEDIA_INVENTORY",
    ]
    for key in required:
        assert key in cases, f"missing corpus case {key}"
        markers = cases[key].get("markers") or []
        assert markers, f"corpus case {key} needs markers"


def test_intelligence_ops_recipes_markers():
    intel_raw = json.loads(
        Path("tv_app/content/vista_agent_intelligence.json").read_text(encoding="utf-8")
    )
    intel_blob = json.dumps(intel_raw, ensure_ascii=False)
    ops = json.loads(
        Path("tv_app/content/presentation_ops_content.json").read_text(encoding="utf-8")
    )
    recipes = json.loads(
        Path("tv_app/content/presentation_recipes.json").read_text(encoding="utf-8")
    )
    ops_blob = json.dumps(ops, ensure_ascii=False)
    recipes_blob = json.dumps(recipes, ensure_ascii=False)
    combined = intel_blob + ops_blob + recipes_blob

    assert "filterDigest" in intel_blob
    assert "re_layer_playlist_filters" in intel_blob
    assert "previewAssetPaste" in intel_blob
    assert "continuous_review" in intel_blob
    assert "re_layer_playlist_filters" in (ops.get("operations") or {})
    assert "apply_published_slide_template" in (ops.get("operations") or {})
    assert "TV_RELAYER_FILTERS" in (recipes.get("recipes") or {})
    assert (intel_raw.get("media_limits") or {}).get("previewAssetPaste")
    assert (intel_raw.get("media_limits") or {}).get("uploadCapability") == "TARGET"

    # Every fixture marker must appear somewhere in JSON SoT (gate = FAIL if missing).
    for case_id, case in (_corpus().get("cases") or {}).items():
        for marker in case.get("markers") or []:
            assert marker in combined, f"{case_id} marker missing in SoT: {marker}"


def test_gate_unit_smoke_no_skip():
    allowed = PresentationOpsContentService.allowed_ops()
    assert "re_layer_playlist_filters" in allowed
    assert "apply_published_slide_template" in allowed
    add_schema = PresentationOpsContentService.operation_spec("add_blank_slide")[
        "inputSchema"
    ]["properties"]
    assert "durationSec" in add_schema
    assert "background" in add_schema

    native = {
        "version": 5,
        "blocks": [
            {
                "id": "a",
                "type": "data_source",
                "dataBinding": {
                    "operationId": "get_on_time_delivery_pct",
                    "params": {"branch": "01", "dateRangePreset": "this_month"},
                },
            },
            {
                "id": "b",
                "type": "data_source",
                "dataBinding": {
                    "operationId": "get_on_time_delivery_pct",
                    "params": {"branch": "01", "dateRangePreset": "this_month"},
                },
            },
        ],
    }
    digest = FilterDigestService.digest_slide(native)
    assert digest["duplicates"]
    apply_relayer(native, scope="slide", keys=None, playlist_defaults={})
    assert native.get("dataFilters")

    route = {"paramStrategy": "date_range", "openEndedDateRange": False, "paramSchema": {}}
    enriched = ReadySlideQualityService.enrich_data_source_params(
        route, {}, playlist_defaults={"dateRangePreset": "this_month"}
    )
    assert "dateRangePreset" not in enriched

    store = EditorFocusStore(ttl_seconds=30)
    store.record(user_id="u1", playlist_id="p1", slide_id="s1")
    with store._lock:
        import time

        store._by_user["u1"]["_mono"] = time.monotonic() - 35
    focus = store.get_for_user("u1")
    assert focus is not None
    assert focus.get("stale") is True

    assert (SLIDE_TEMPLATES_DIR / "system-estoque-top5.mdd").is_file()
    assert (SLIDE_TEMPLATES_DIR / "system-oee-overview.mdd").is_file()
    assert "TV_RELAYER_FILTERS" in PresentationRecipeService.document().get("recipes", {})

    directives = VistaAgentIntelligenceService.agent_directives()
    assert "filter_layering" in directives
    assert "continuous_review" in directives


if __name__ == "__main__":
    pytest.main([__file__, "-q"])
