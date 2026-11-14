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
# AC-MP — query-scope identity for multipage union
# -------------------------------------------------------------------


def test_scope_pairs_exclude_window_keys():
    """Pages of one query differ ONLY in window args — pagination
    selectors never enter the scope fingerprint."""
    from app.application.capability_provision.semantic_capability_support import (
        _invocation_scope,
    )

    page1 = _invocation_scope(
        {"entity": "process", "action": "search",
         "params": {"status": "ativo"}, "page": 1, "limit": 40}
    )
    page2 = _invocation_scope(
        {"entity": "process", "action": "search",
         "params": {"status": "ativo"}, "page": 2, "offset": 40}
    )
    assert page1 == page2
    assert "params.status=ativo" in page1


def test_scope_pairs_distinguish_filters():
    """Different filters → different scope → never unionable."""
    from app.application.capability_provision.semantic_capability_support import (
        _invocation_scope,
    )

    active = _invocation_scope({"params": {"status": "ativo"}})
    inactive = _invocation_scope({"params": {"status": "inativo"}})
    assert active != inactive


def test_scope_pairs_scalar_list_order_insensitive():
    """`{status:[a,b]}` vs `{status:[b,a]}` — same logical scope."""
    from app.application.capability_provision.semantic_capability_support import (
        _invocation_scope,
    )

    assert _invocation_scope(
        {"params": {"status": ["ativo", "inativo"]}}
    ) == _invocation_scope(
        {"params": {"status": ["inativo", "ativo"]}}
    )


def test_scope_pairs_opaque_values_stay_distinguishable():
    """Unrepresentable values digest — different payloads never
    collapse into one empty scope."""
    from app.application.capability_provision.semantic_capability_support import (
        _invocation_scope,
    )

    left = _invocation_scope({"params": {"filter": {"x"}}})
    right = _invocation_scope({"params": {"filter": {"y"}}})
    assert left != right
    assert left and right

_SCOPE_ACTIVE = ("entity=process", "params.status=ativo")
_SCOPE_INACTIVE = ("entity=process", "params.status=inativo")


def _scoped_page(
    *, start: int, count: int, total: int, scope: tuple, **kwargs
):
    return _attempt(
        entity="process",
        vocabulary=("process", "search"),
        items=[
            {"code": f"PROC-{i:04d}"} for i in range(start, start + count)
        ],
        total=total,
        scope=scope,
        **kwargs,
    )


def test_mp01_cross_scope_filters_not_unionable():
    """AC-MP-01/02 — `status=ativo` page + `status=inativo` page with
    the same declared total: distinct records do not prove one query
    (SAME_TOTAL + DISTINCT != PROVEN_SAME_QUERY_COMPLETENESS)."""
    obligation = _ob("list of processes", source="process")
    pages = (
        _scoped_page(start=0, count=60, total=109, scope=_SCOPE_ACTIVE),
        _scoped_page(start=60, count=49, total=109, scope=_SCOPE_INACTIVE),
    )
    coverage = _coverage(
        (obligation,), pages, delivery="enumeration"
    )
    assert coverage[obligation.description] == OBLIGATION_INCONCLUSIVE


def test_mp02_partial_scope_presence_not_unionable():
    """A scoped page plus a scope-empty page: the absent scope cannot
    be assumed equal to the declared one — fail closed."""
    obligation = _ob("list of processes", source="process")
    pages = (
        _scoped_page(start=0, count=60, total=109, scope=_SCOPE_ACTIVE),
        _scoped_page(start=60, count=49, total=109, scope=()),
    )
    coverage = _coverage(
        (obligation,), pages, delivery="enumeration"
    )
    assert coverage[obligation.description] == OBLIGATION_INCONCLUSIVE


def test_mp03_different_owner_not_unionable():
    """AC-MP-03 — same anchor echo + same total across different
    specialists is coincidence, not one query."""
    obligation = _ob("list of processes", source="process")
    pages = (
        _scoped_page(
            start=0, count=60, total=109,
            scope=_SCOPE_ACTIVE, specialist="teo",
        ),
        _scoped_page(
            start=60, count=49, total=109,
            scope=_SCOPE_ACTIVE, specialist="davi",
        ),
    )
    coverage = _coverage(
        (obligation,), pages, delivery="enumeration"
    )
    assert coverage[obligation.description] == OBLIGATION_INCONCLUSIVE


def test_mp04_different_capability_not_unionable():
    """AC-MP-04 — different remote capabilities echoing the same
    anchor cannot fabricate one collection."""
    obligation = _ob("list of processes", source="process")
    pages = (
        _scoped_page(
            start=0, count=60, total=109,
            scope=_SCOPE_ACTIVE, remote="search",
        ),
        _scoped_page(
            start=60, count=49, total=109,
            scope=_SCOPE_ACTIVE, remote="export",
        ),
    )
    coverage = _coverage(
        (obligation,), pages, delivery="enumeration"
    )
    assert coverage[obligation.description] == OBLIGATION_INCONCLUSIVE


def test_mp05_same_scope_pages_unionable():
    """AC-MP-05 — pages of the SAME declared scope (identical filter
    pairs) covering the single declared total demonstrate the
    enumeration."""
    obligation = _ob("list of processes", source="process")
    pages = (
        _scoped_page(start=0, count=40, total=109, scope=_SCOPE_ACTIVE),
        _scoped_page(start=40, count=40, total=109, scope=_SCOPE_ACTIVE),
        _scoped_page(start=80, count=29, total=109, scope=_SCOPE_ACTIVE),
    )
    coverage = _coverage(
        (obligation,), pages, delivery="enumeration"
    )
    assert coverage[obligation.description] == OBLIGATION_SATISFIED


def test_mp07_scoped_overlap_not_demonstrated():
    """AC-MP-07 — overlapping pages of one scope cannot inflate the
    union toward the total."""
    obligation = _ob("list of processes", source="process")
    pages = (
        _scoped_page(start=0, count=60, total=109, scope=_SCOPE_ACTIVE),
        _scoped_page(start=0, count=60, total=109, scope=_SCOPE_ACTIVE),
    )
    coverage = _coverage(
        (obligation,), pages, delivery="enumeration"
    )
    assert coverage[obligation.description] == OBLIGATION_INCONCLUSIVE


def test_mp08_record_identity_presentation_variance():
    """AC-MP-08 — the same record re-rendered with different payload
    fields counts once: owner record identity, not full-content
    fingerprint, deduplicates."""
    obligation = _ob("list of processes", source="process")
    pages = (
        _attempt(
            entity="process",
            vocabulary=("process", "search"),
            items=[
                {"code": "PROC-A", "name": "Avaliacao"},
                {"code": "PROC-B"},
            ],
            total=3,
            scope=_SCOPE_ACTIVE,
        ),
        _attempt(
            entity="process",
            vocabulary=("process", "search"),
            items=[
                {"code": "PROC-A", "name": "Avaliacao (revisada)"},
                {"code": "PROC-C"},
            ],
            total=3,
            scope=_SCOPE_ACTIVE,
        ),
    )
    coverage = _coverage(
        (obligation,), pages, delivery="enumeration"
    )
    assert coverage[obligation.description] == OBLIGATION_SATISFIED


def test_mp09_distinct_records_same_rendering_not_merged():
    """AC-MP-09 — records with distinct owner ids and identical
    rendered payloads stay distinct; id-less identical payloads
    collapse conservatively (undercount only fails closed)."""
    obligation = _ob("list of processes", source="process")
    pages = (
        _attempt(
            entity="process",
            vocabulary=("process", "search"),
            items=[
                {"id": "1", "label": "same"},
                {"id": "2", "label": "same"},
            ],
            total=4,
            scope=_SCOPE_ACTIVE,
        ),
        _attempt(
            entity="process",
            vocabulary=("process", "search"),
            items=[
                {"id": "3", "label": "same"},
                {"id": "4", "label": "same"},
            ],
            total=4,
            scope=_SCOPE_ACTIVE,
        ),
    )
    coverage = _coverage(
        (obligation,), pages, delivery="enumeration"
    )
    assert coverage[obligation.description] == OBLIGATION_SATISFIED


def test_mp09_idless_identical_payloads_fail_closed():
    obligation = _ob("list of processes", source="process")
    pages = (
        _attempt(
            entity="process",
            vocabulary=("process", "search"),
            items=[{"label": "same"}, {"label": "same"}],
            total=4,
            scope=_SCOPE_ACTIVE,
        ),
        _attempt(
            entity="process",
            vocabulary=("process", "search"),
            items=[{"label": "same"}, {"label": "same"}],
            total=4,
            scope=_SCOPE_ACTIVE,
        ),
    )
    coverage = _coverage(
        (obligation,), pages, delivery="enumeration"
    )
    assert coverage[obligation.description] == OBLIGATION_INCONCLUSIVE


def test_mp13_owner_incomplete_flag_beats_numeric_coverage():
    """AC-MP-13 — `is_complete:false` inside one result is an owner
    declaration of incompleteness; delivered==total cannot annul it."""
    obligation = _ob("list of processes", source="process")
    attempt = _attempt(
        entity="process",
        vocabulary=("process", "search"),
        items=[{"code": f"PROC-{i:04d}"} for i in range(20)],
        total=20,
        data_complete=False,
    )
    coverage = _coverage(
        (obligation,), (attempt,), delivery="enumeration"
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
