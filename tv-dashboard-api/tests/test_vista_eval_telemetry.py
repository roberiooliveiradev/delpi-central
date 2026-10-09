"""P7 — eval catalog + quality telemetry gates (roadmap §35/§41).

Covers: catalog completeness, corpus coverage, telemetry privacy/cardinality,
non-semantic behavior (telemetry failure never alters product output),
snapshot/reset semantics.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from tests.solution_intelligence_corpus import P6_CORPUS
from tests.vista_metric_catalog import (
    EVAL_CORPUS_VERSION,
    FORBIDDEN_TELEMETRY_KEYS,
    MEASURABLE_NOW,
    NEEDS_FIXTURE,
    NEEDS_HUMAN_RUBRIC,
    NEEDS_TELEMETRY,
    VISTA_METRIC_CATALOG,
)
from tv_app.application.gpt_actions.dispatch_service import (
    GptActionsDispatchService,
)
from tv_app.application.services.data.vista_quality_telemetry import (
    _FIELD_ALLOWLIST,
    record_grounding,
    record_quality_event,
    record_route_search,
    reset_vista_quality_telemetry,
    vista_quality_telemetry_snapshot,
)


@pytest.fixture(autouse=True)
def _clean():
    reset_vista_quality_telemetry()
    yield
    reset_vista_quality_telemetry()


# --- metric catalog --------------------------------------------------------


def test_catalog_covers_all_p7_dimensions():
    required = {
        "OBJECT_GROUNDING",
        "CREATE_VS_ALTER",
        "CLARIFICATION_CORRECTNESS",
        "TARGET_RESOLUTION",
        "DATA_ROUTE_RETRIEVAL",
        "DATA_DIAGNOSIS",
        "VISUAL_SELECTION",
        "FILTER_LAYERING",
        "DISPLAY_FORMAT_SELECTION",
        "TYPED_OP_VALIDITY",
        "PROPOSAL_VALIDITY",
        "WRITE_SAFETY",
        "VERIFY_OUTCOME",
        "USER_CORRECTION",
        "TRANSPORT_PARITY",
    }
    assert required <= set(VISTA_METRIC_CATALOG)


def test_catalog_entries_have_full_semantics():
    for dim_id, meta in VISTA_METRIC_CATALOG.items():
        for key in (
            "purpose",
            "measurementSource",
            "numerator",
            "denominator",
            "exclusions",
            "evidence",
            "status",
        ):
            assert meta.get(key), f"{dim_id}.{key} missing"
        assert meta["status"] in {
            MEASURABLE_NOW,
            NEEDS_FIXTURE,
            NEEDS_TELEMETRY,
            NEEDS_HUMAN_RUBRIC,
        }


def test_user_correction_not_fabricated():
    # No deterministic correction signal exists — honest NEEDS_TELEMETRY.
    assert VISTA_METRIC_CATALOG["USER_CORRECTION"]["status"] == NEEDS_TELEMETRY


def test_corpus_coverage_no_silent_dimension():
    covered = set()
    for meta in VISTA_METRIC_CATALOG.values():
        src = meta["measurementSource"]
        if src.startswith(("suite:", "corpus:", "telemetry:")):
            covered.add(src)
        elif meta["status"] in {NEEDS_FIXTURE, NEEDS_TELEMETRY, NEEDS_HUMAN_RUBRIC}:
            covered.add(meta["status"])
    assert len(VISTA_METRIC_CATALOG) > 0
    for meta in VISTA_METRIC_CATALOG.values():
        assert meta["measurementSource"] in covered or meta["status"] in covered


# --- telemetry privacy / cardinality ---------------------------------------


def test_no_forbidden_keys_in_snapshot():
    record_grounding(
        selection_state="ACTIVE", resolved=2, missing=0
    )
    record_route_search(
        tv_route_hit=False,
        solution_lookup_used=True,
        gap_classification="NO_SOLUTION_EVIDENCE",
        candidates=0,
    )
    snap = vista_quality_telemetry_snapshot()
    for event in snap["recent"]:
        assert not FORBIDDEN_TELEMETRY_KEYS & set(event)
        for value in event.values():
            assert not isinstance(value, (dict, list))


def test_unknown_family_and_fields_dropped():
    record_quality_event("nonsense", anything="x")
    record_grounding(selection_state="ACTIVE", resolved=1, missing=0)
    snap = vista_quality_telemetry_snapshot()
    assert all(e["family"] != "nonsense" for e in snap["recent"])
    grounding = [e for e in snap["recent"] if e["family"] == "grounding"]
    assert set(grounding[0]) - {"ts", "schema", "family"} <= set(
        _FIELD_ALLOWLIST["grounding"]
    )


def test_buckets_keep_low_cardinality():
    for n in range(10):
        record_grounding(selection_state="ACTIVE", resolved=n, missing=n)
    snap = vista_quality_telemetry_snapshot()
    bucket_keys = [k for k in snap["counts"] if "resolvedBucket" in k]
    assert len(bucket_keys) <= 4  # 0,1,2,3+


def test_fail_open_recorder_never_raises():
    record_quality_event("grounding", selectionState={"weird": "object"})
    record_route_search(
        tv_route_hit=None,
        solution_lookup_used=True,
        gap_classification=12345,
        candidates="x",
    )
    assert vista_quality_telemetry_snapshot()["counts"]


# --- telemetry is non-semantic ----------------------------------------------


def _dispatch(suggestions):
    class _S:
        def suggest(self, *, query, limit, category=None):
            return {"suggestions": list(suggestions)}

    return GptActionsDispatchService(
        repo=MagicMock(), writes=MagicMock(), commit=MagicMock(), suggest=_S()
    )


def test_telemetry_failure_does_not_change_product_output(monkeypatch):
    import tv_app.application.services.data.vista_quality_telemetry as tq

    dispatch = _dispatch([])
    user = SimpleNamespace(is_superadmin=True, permissions=[], id="u")

    base = dispatch.search_data_routes(user=user, query="ebitda", limit=8)

    class _BoomDeque:
        """Internal sink that raises on append — recorder must swallow it."""

        maxlen = 500

        def append(self, _item):
            raise RuntimeError("telemetry down")

        def clear(self):
            pass

        def __iter__(self):
            return iter(())

    monkeypatch.setattr(tq, "_events", _BoomDeque())
    out = dispatch.search_data_routes(user=user, query="ebitda", limit=8)
    assert out["total"] == base["total"]
    assert out["searchMissDoesNotProveAbsence"] is True


def test_route_search_records_bounded_event():
    dispatch = _dispatch([])
    user = SimpleNamespace(is_superadmin=True, permissions=[], id="u")
    dispatch.search_data_routes(user=user, query="ebitda", limit=8)
    snap = vista_quality_telemetry_snapshot()
    route_events = [e for e in snap["recent"] if e["family"] == "route_search"]
    assert len(route_events) == 1
    event = route_events[0]
    assert event["tvRouteHit"] is False
    assert event["solutionLookupUsed"] is False  # no gateway injected here
    assert event["gapClassification"] == "CONTRACT_GAP"  # fail-closed
    assert event["candidateBucket"] in {"0", "1", "2", "3+"}


def test_route_hit_records_without_solution_lookup():
    dispatch = _dispatch([{"operationId": "op", "label": "x"}])
    user = SimpleNamespace(is_superadmin=True, permissions=[], id="u")
    dispatch.search_data_routes(user=user, query="otd", limit=8)
    event = [
        e
        for e in vista_quality_telemetry_snapshot()["recent"]
        if e["family"] == "route_search"
    ][0]
    assert event["tvRouteHit"] is True
    assert event["solutionLookupUsed"] is False
    assert event["gapClassification"] == "TV_ROUTE_FOUND"


def test_snapshot_counts_increment():
    before = vista_quality_telemetry_snapshot()["counts"].get(
        "route_search.events", 0
    )
    dispatch = _dispatch([])
    user = SimpleNamespace(is_superadmin=True, permissions=[], id="u")
    dispatch.search_data_routes(user=user, query="ebitda", limit=8)
    after = vista_quality_telemetry_snapshot()["counts"]["route_search.events"]
    assert after == before + 1


def test_corpus_still_frozen():
    # Guard: P6 corpus semantics unchanged by P7 instrumentation.
    ids = [c["id"] for c in P6_CORPUS]
    assert len(ids) == len(set(ids)) == 12
