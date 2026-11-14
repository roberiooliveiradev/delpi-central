"""INT-2 final coverage — delivery completeness vs obligation verdict.

Task
DELIA-C3-T2-INT2-FINAL-COVERAGE-DELIVERY-AND-AGGREGATION-GATE-01:

- OBLIGATION_DEMONSTRATED != REQUEST_DELIVERY_COMPLETE — but an
  enumeration obligation bound to a PROVABLY PARTIAL collection
  (declared total > delivered items, is_complete=false, truncated) is
  not demonstrated: the evidence is pertinent yet incomplete.
- AUTHORITATIVE_AGGREGATE + correct scope + verified evidence →
  legitimate SATISFIED: the owner-declared metric is the deliverable;
  a partial items window does not invalidate the count.
- Delivery kind comes from the typed plan (``goal.output_mode``) and is
  threaded into the obligation evaluator — no parallel classifier.
"""

from __future__ import annotations

from app.application.capability_provision.semantic_capability_support import (
    OBLIGATION_INCONCLUSIVE,
    OBLIGATION_SATISFIED,
    MaterialObligation,
    _evaluate_material_obligations,
)
from tests.test_rc5_anchor_correctness_remediation import (
    _attempt,
    _ob,
)


def _coverage(obligations, business, delivery=None):
    kwargs = {"obligations": obligations, "business": business}
    if delivery is not None:
        kwargs["delivery"] = delivery
    return dict(
        _evaluate_material_obligations(**kwargs)
    )


# -------------------------------------------------------------------
# AC-INT2-F01/F02 — enumeration: partial retrieval never demonstrates
# -------------------------------------------------------------------


def test_f02_enumeration_partial_window_is_not_demonstrated():
    """`total:109, items:20` — owner declares more records than it
    delivered; the anchored enumeration obligation cannot be
    SATISFIED: evidence is pertinent but acquisition is incomplete."""
    obligation = _ob("list of processes", source="process")
    attempt = _attempt(
        entity="process",
        vocabulary=("process", "search"),
        items=[{"code": f"PROC-{i:04d}"} for i in range(20)],
        total=109,
    )
    coverage = _coverage(
        (obligation,), (attempt,), delivery="enumeration"
    )
    assert coverage[obligation.description] == OBLIGATION_INCONCLUSIVE


def test_f01_enumeration_fully_retrieved_is_demonstrated():
    """`total:20, items:20` — delivered window covers the declared
    total; legitimate SATISFIED."""
    obligation = _ob("list of processes", source="process")
    attempt = _attempt(
        entity="process",
        vocabulary=("process", "search"),
        items=[{"code": f"PROC-{i:04d}"} for i in range(20)],
        total=20,
    )
    coverage = _coverage(
        (obligation,), (attempt,), delivery="enumeration"
    )
    assert coverage[obligation.description] == OBLIGATION_SATISFIED


def test_f02_enumeration_owner_declared_incomplete():
    obligation = _ob("list of processes", source="process")
    attempt = _attempt(
        entity="process",
        vocabulary=("process", "search"),
        items=[{"code": "PROC-0001"}],
        total=1,
        data_complete=False,
    )
    coverage = _coverage(
        (obligation,), (attempt,), delivery="enumeration"
    )
    assert coverage[obligation.description] == OBLIGATION_INCONCLUSIVE


def test_f02_enumeration_owner_declared_truncated():
    obligation = _ob("list of processes", source="process")
    attempt = _attempt(
        entity="process",
        vocabulary=("process", "search"),
        items=[{"code": "PROC-0001"}],
        total=1,
        truncated=True,
    )
    coverage = _coverage(
        (obligation,), (attempt,), delivery="enumeration"
    )
    assert coverage[obligation.description] == OBLIGATION_INCONCLUSIVE


def test_f03_enumeration_unknown_completeness_not_demonstrated():
    """UNKNOWN_COMPLETENESS != PROVEN_COMPLETE — an unmarked collection
    (no total, no is_complete, no truncation flag) cannot demonstrate
    an enumeration: pertinent but unverifiable coverage → INCONCLUSIVE."""
    obligation = _ob("list of processes", source="process")
    attempt = _attempt(
        entity="process",
        vocabulary=("process", "search"),
        structured={
            "entity": "process",
            "shape": "record_list",
            "data": {"items": [{"code": "PROC-0001"}]},
        },
    )
    coverage = _coverage(
        (obligation,), (attempt,), delivery="enumeration"
    )
    assert coverage[obligation.description] == OBLIGATION_INCONCLUSIVE


def test_tc04_enumeration_explicit_complete_marker_demonstrates():
    """AC-TC-04 — the owner's explicit ``is_complete`` marker is a
    legitimate completeness proof without a numeric total."""
    obligation = _ob("list of processes", source="process")
    attempt = _attempt(
        entity="process",
        vocabulary=("process", "search"),
        structured={
            "entity": "process",
            "shape": "paged_list",
            "data": {
                "items": [{"code": "PROC-0001"}, {"code": "PROC-0002"}],
                "is_complete": True,
                "truncated": False,
            },
        },
    )
    coverage = _coverage(
        (obligation,), (attempt,), delivery="enumeration"
    )
    assert coverage[obligation.description] == OBLIGATION_SATISFIED


def test_tc_enumeration_non_collection_evidence_not_demonstrated():
    """A bare record carries no collection — nothing enumerable can be
    proven complete from it."""
    obligation = _ob("list of processes", source="process")
    attempt = _attempt(
        entity="process",
        vocabulary=("process", "detail"),
        structured={
            "entity": "process",
            "shape": "record",
            "data": {"code": "PROC-0001", "name": "Avaliações"},
        },
    )
    coverage = _coverage(
        (obligation,), (attempt,), delivery="enumeration"
    )
    assert coverage[obligation.description] == OBLIGATION_INCONCLUSIVE


# -------------------------------------------------------------------
# AC-TC-05/06/07 — multipage coverage
# -------------------------------------------------------------------


def _page(*, start: int, count: int, total: int):
    return _attempt(
        entity="process",
        vocabulary=("process", "search"),
        items=[
            {"code": f"PROC-{i:04d}"} for i in range(start, start + count)
        ],
        total=total,
    )


def test_tc05_multipage_union_covers_total():
    """40+40+29 distinct pages of the same scope covering the declared
    total — set continuity + identity proven → SATISFIED."""
    obligation = _ob("list of processes", source="process")
    pages = (
        _page(start=0, count=40, total=109),
        _page(start=40, count=40, total=109),
        _page(start=80, count=29, total=109),
    )
    coverage = _coverage(
        (obligation,), pages, delivery="enumeration"
    )
    assert coverage[obligation.description] == OBLIGATION_SATISFIED


def test_tc06_multipage_gap_not_demonstrated():
    """A missing page (60 distinct of 109) cannot fabricate coverage."""
    obligation = _ob("list of processes", source="process")
    pages = (
        _page(start=0, count=40, total=109),
        _page(start=80, count=20, total=109),
    )
    coverage = _coverage(
        (obligation,), pages, delivery="enumeration"
    )
    assert coverage[obligation.description] == OBLIGATION_INCONCLUSIVE


def test_tc07_multipage_duplicates_not_demonstrated():
    """40+40+29 with overlapping records — raw arithmetic != coverage."""
    obligation = _ob("list of processes", source="process")
    pages = (
        _page(start=0, count=40, total=109),
        _page(start=0, count=40, total=109),  # same records again
        _page(start=80, count=29, total=109),
    )
    coverage = _coverage(
        (obligation,), pages, delivery="enumeration"
    )
    assert coverage[obligation.description] == OBLIGATION_INCONCLUSIVE


def test_tc08_multipage_divergent_totals_not_demonstrated():
    """Pages declaring different totals are not provably one set."""
    obligation = _ob("list of processes", source="process")
    pages = (
        _page(start=0, count=60, total=109),
        _page(start=60, count=49, total=200),
    )
    coverage = _coverage(
        (obligation,), pages, delivery="enumeration"
    )
    assert coverage[obligation.description] == OBLIGATION_INCONCLUSIVE


# -------------------------------------------------------------------
# AC-INT2-F04/F05 — aggregation: authoritative metric is the deliverable
# -------------------------------------------------------------------


def test_f04_aggregation_authoritative_total_is_demonstrated():
    """`total:109` is the owner-declared metric — a partial items
    window does not invalidate an authoritative count."""
    obligation = _ob("count of processes", source="process")
    attempt = _attempt(
        entity="process",
        vocabulary=("process", "search"),
        items=[{"code": f"PROC-{i:04d}"} for i in range(20)],
        total=109,
    )
    coverage = _coverage(
        (obligation,), (attempt,), delivery="aggregation"
    )
    assert coverage[obligation.description] == OBLIGATION_SATISFIED


def test_f04_aggregation_complete_collection_count_derivable():
    """A provably complete collection (is_complete, no truncation, no
    contradicting total) yields a mechanically derivable count."""
    obligation = _ob("count of processes", source="process")
    attempt = _attempt(
        entity="process",
        vocabulary=("process", "search"),
        structured={
            "entity": "process",
            "shape": "paged_list",
            "data": {
                "items": [{"code": "PROC-0001"}, {"code": "PROC-0002"}],
                "is_complete": True,
                "truncated": False,
            },
        },
    )
    coverage = _coverage(
        (obligation,), (attempt,), delivery="aggregation"
    )
    assert coverage[obligation.description] == OBLIGATION_SATISFIED


def test_f05_aggregation_unverifiable_collection():
    """No declared metric AND unverifiable collection completeness —
    the count cannot be invented from an unproven window."""
    obligation = _ob("count of processes", source="process")
    attempt = _attempt(
        entity="process",
        vocabulary=("process", "search"),
        structured={
            "entity": "process",
            "shape": "paged_list",
            "data": {"items": [{"code": "PROC-0001"}]},
        },
    )
    coverage = _coverage(
        (obligation,), (attempt,), delivery="aggregation"
    )
    assert coverage[obligation.description] == OBLIGATION_INCONCLUSIVE


def test_f05_aggregation_record_without_metric():
    """A bound record carrying no aggregate field and no collection —
    nothing demonstrates the requested metric."""
    obligation = _ob("count of processes", source="process")
    attempt = _attempt(
        entity="process",
        vocabulary=("process", "detail"),
        structured={
            "entity": "process",
            "shape": "record",
            "data": {"code": "PROC-0001", "name": "Avaliações"},
        },
    )
    coverage = _coverage(
        (obligation,), (attempt,), delivery="aggregation"
    )
    assert coverage[obligation.description] == OBLIGATION_INCONCLUSIVE


# -------------------------------------------------------------------
# AC-INT2-F11 — delivery kinds stay orthogonal
# -------------------------------------------------------------------


def test_f11_record_detail_not_demoted_by_collection_window():
    """Delivery kind is a scope discriminator: a record_detail
    obligation bound to a partial collection window still demonstrates
    the record kind — completeness gating is enumeration-scoped."""
    obligation = _ob("process detail", source="process")
    attempt = _attempt(
        entity="process",
        vocabulary=("process", "detail"),
        items=[{"code": "PROC-0001"}],
        total=109,
    )
    coverage = _coverage(
        (obligation,), (attempt,), delivery="record_detail"
    )
    assert coverage[obligation.description] == OBLIGATION_SATISFIED


def test_f11_unspecified_delivery_keeps_prior_semantics():
    obligation = _ob("list of processes", source="process")
    attempt = _attempt(
        entity="process",
        vocabulary=("process", "search"),
        items=[{"code": "PROC-0001"}],
        total=109,
    )
    coverage = _coverage(
        (obligation,), (attempt,), delivery="unspecified"
    )
    assert coverage[obligation.description] == OBLIGATION_SATISFIED


def test_f12_no_delivery_param_keeps_prior_semantics():
    """Callers without the typed delivery context keep the pre-existing
    verdict semantics (backward-compatible extension)."""
    obligation = _ob("list of processes", source="process")
    attempt = _attempt(
        entity="process",
        vocabulary=("process", "search"),
        items=[{"code": "PROC-0001"}],
        total=109,
    )
    coverage = dict(
        _evaluate_material_obligations(
            obligations=(obligation,), business=(attempt,)
        )
    )
    assert coverage[obligation.description] == OBLIGATION_SATISFIED
