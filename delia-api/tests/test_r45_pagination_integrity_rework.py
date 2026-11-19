"""R5 integrity rework — page completeness and count honesty (doc 43).

TASK: DELIA-C3-R45-PAGINATION-INTEGRITY-AND-PRODUCTION-SSH-VALIDATION-01

Locks unsafe edges from independent review, re-anchored on the wired
authoritative mechanisms (E2: the standalone ``aggregate_paginated_pages``
oracle was retired — it had zero application consumers):

- ``_joint_collection_coverage`` is the connected multipage evaluator:
  a collection is complete only when the deduplicated record union of
  successful, scope-consistent attempts equals a single owner-declared
  total. Order, page arithmetic and ``has_more`` narration never prove
  completeness by themselves.
- ``extract_pagination_envelope`` + ``resolve_count_semantics`` carry
  count honesty: ``has_more=None`` never proves complete, an isolated
  page>1 is not the query total, and gaps/failures never fabricate one.
"""

from __future__ import annotations

from typing import Any

from app.application.capability_provision.generic_evidence_renderer import (
    CountResolutionKind,
    UNKNOWN_TOTAL_MESSAGE,
    extract_pagination_envelope,
    resolve_count_semantics,
)
from app.application.capability_provision.semantic_capability_support import (
    MaterialObligation,
    _joint_collection_coverage,
)
from app.application.interaction.capability_attempt import (
    GovernedCapabilityStatus,
)

from tests.test_f2_native_refactor_e1 import _paged_attempt


def _page(
    *,
    n: int = 10,
    page: int | None = 1,
    page_size: int = 10,
    has_more: bool | None = True,
    total_count: int | None = None,
    id_offset: int = 0,
    omit_ids: bool = False,
) -> dict[str, Any]:
    items = []
    for i in range(n):
        row: dict[str, Any] = {"title": f"T{id_offset + i + 1}"}
        if not omit_ids:
            row["id"] = id_offset + i + 1
        items.append(row)
    payload: dict[str, Any] = {"items": items}
    if page is not None:
        payload["page"] = page
    if page_size is not None:
        payload["page_size"] = page_size
    if has_more is not None:
        payload["has_more"] = has_more
    if total_count is not None:
        payload["total_count"] = total_count
    return payload


def _records(start: int, n: int, *, ids: bool = True) -> list[dict]:
    if ids:
        return [{"id": i} for i in range(start, start + n)]
    return [{"title": f"r{i}"} for i in range(start, start + n)]


def _obl() -> MaterialObligation:
    return MaterialObligation(
        description="enumerate items", evidence_source="items"
    )


def _coverage(attempts) -> bool:
    return bool(_joint_collection_coverage(_obl(), tuple(attempts)))


def test_r45r_t01_no_has_more_no_total():
    envelope = extract_pagination_envelope(
        {"items": [{"id": 1}, {"id": 2}], "page": 1, "page_size": 2}
    )
    assert envelope is not None
    assert envelope.has_more is None
    resolution = resolve_count_semantics(envelope)
    assert resolution.total is None
    assert resolution.kind is CountResolutionKind.PAGE_SLICE_NOT_TOTAL

    # An unmarked collection (no declared total) is unverifiable —
    # the wired evaluator must not promote it to complete.
    assert not _coverage([_paged_attempt(_records(1, 2), None)])


def test_r45r_t02_last_page_only():
    envelope = extract_pagination_envelope(
        _page(n=4, page=3, has_more=False, id_offset=20)
    )
    resolution = resolve_count_semantics(envelope)
    assert resolution.total is None
    assert resolution.kind is CountResolutionKind.PARTIAL_UNKNOWN
    assert UNKNOWN_TOTAL_MESSAGE in resolution.message


def test_r45r_t03_complete_two_page_walk():
    # 1-10 + 11-20 with a single consistent declared total of 20 —
    # union == total ⇒ complete.
    assert _coverage([
        _paged_attempt(_records(1, 10), 20),
        _paged_attempt(_records(11, 10), 20),
    ])


def test_r45r_t04_missing_intermediate_page():
    # Owner total 25 but union covers 15 → never complete.
    assert not _coverage([
        _paged_attempt(_records(1, 10), 25),
        _paged_attempt(_records(21, 5), 25),
    ])


def test_r45r_t05_duplicate_page():
    # Same records re-observed: union 5 ≠ declared 10 → not complete.
    assert not _coverage([
        _paged_attempt(_records(1, 5), 10),
        _paged_attempt(_records(1, 5), 10),
    ])


def test_r45r_t06_duplicate_ticket_id():
    # Overlapping identity shrinks the union below the declared total.
    assert not _coverage([
        _paged_attempt(_records(1, 10), 15),
        _paged_attempt([{"id": 1}, *_records(11, 4)], 15),
    ])


def test_r45r_t07_malformed_page():
    # An attempt without declared total is unverifiable — paired with a
    # partial slice it can never prove completeness.
    assert not _coverage([
        _paged_attempt(_records(1, 10), 10),
        _paged_attempt(_records(11, 5), None),
    ])


def test_r45r_t08_page_failure():
    # A failed attempt contributes nothing; a single partial slice
    # cannot satisfy the declared total.
    import dataclasses as _dc

    failed = _dc.replace(
        _paged_attempt(_records(11, 5), 15),
        status=GovernedCapabilityStatus.SOURCE_UNAVAILABLE,
    )
    assert not _coverage([
        _paged_attempt(_records(1, 10), 15),
        failed,
    ])


def test_r45r_t09_max_pages_exceeded():
    # Budget-capped walk: collected pages are a strict subset of the
    # declared total → never complete (the bound lives in the governed
    # orchestration loop, not in the evaluator).
    assert not _coverage([
        _paged_attempt(_records(1, 10), 50),
        _paged_attempt(_records(11, 10), 50),
        _paged_attempt(_records(21, 10), 50),
    ])


def test_r45r_t10_budget_exhausted_same_as_partial():
    # Two pages with has_more still open and union < total → partial.
    assert not _coverage([
        _paged_attempt(_records(1, 10), 20),
        _paged_attempt(_records(11, 5), 20),
    ])


def test_r45r_t11_authoritative_total():
    envelope = extract_pagination_envelope(
        _page(n=10, page=1, has_more=True, total_count=47)
    )
    resolution = resolve_count_semantics(envelope)
    assert resolution.kind is CountResolutionKind.AUTHORITATIVE_TOTAL
    assert resolution.total == 47


def test_r45r_t12_authoritative_total_conflict():
    # Two attempts declaring different totals for the same collection —
    # no single authoritative total ⇒ never complete.
    assert not _coverage([
        _paged_attempt(_records(1, 10), 47),
        _paged_attempt(_records(11, 10), 50),
    ])


def test_r45r_t13_missing_stable_ids():
    # Records without stable identity cannot be unioned reliably —
    # fail closed.
    assert not _coverage([
        _paged_attempt(_records(1, 3, ids=False), 3),
        _paged_attempt(_records(4, 3, ids=False), 3),
    ])


def test_r45r_t14_filter_consistency_status_preserved():
    payload = _page(n=2, page=1, has_more=False)
    for item in payload["items"]:
        item["status"] = "open"
    envelope = extract_pagination_envelope(payload)
    resolution = resolve_count_semantics(envelope)
    assert resolution.total == 2
    assert all(i["status"] == "open" for i in envelope.items)


def test_r45r_t15_concurrent_mutation_via_duplicate_overlap():
    # Overlap that collapses the union below the declared total ⇒
    # unknown, never a recomputed total from merged lengths.
    assert not _coverage([
        _paged_attempt(_records(1, 10), 20),
        _paged_attempt(_records(6, 10), 20),
    ])


def test_r45r_t18_no_material_act():
    assert "ACT" not in UNKNOWN_TOTAL_MESSAGE


def test_r45r_t19_nested_pagination_block_owner_contract():
    # Owner wire shape (transformometro record_read paginated path):
    # page metadata lives inside a nested ``pagination`` block next to
    # ``items`` — the extractor must surface the declared envelope, not
    # drop it as unsigned.
    structured = {
        "data": {
            "total": 109,
            "items": [{"id": f"proc-{i}"} for i in range(40)],
            "pagination": {"page": 1, "page_size": 40, "has_more": True},
            "filters_applied": {"action": "search"},
        }
    }
    envelope = extract_pagination_envelope(structured)
    assert envelope is not None
    assert envelope.page == 1
    assert envelope.page_size == 40
    assert envelope.has_more is True
    assert envelope.total_count == 109
    assert len(envelope.items) == 40


def test_r45r_t20_owner_declared_truncated_marks_incomplete():
    # Owner-declared truncation (``truncated: true`` next to a capped
    # ``items`` list) plus an authoritative total proves more rows
    # exist — ``has_more`` must not stay unsigned while the contract
    # offers page params.
    structured = {
        "data": {
            "total": 109,
            "items": [{"id": f"proc-{i}"} for i in range(40)],
            "truncated": True,
            "returned": 40,
        }
    }
    envelope = extract_pagination_envelope(structured)
    assert envelope is not None
    assert envelope.has_more is True
    assert envelope.total_count == 109


def test_r45r_t21_nested_last_page_signed_complete():
    structured = {
        "data": {
            "total": 109,
            "items": [{"id": f"proc-{i}"} for i in range(29)],
            "pagination": {"page": 3, "page_size": 40, "has_more": False},
        }
    }
    envelope = extract_pagination_envelope(structured)
    assert envelope is not None
    assert envelope.page == 3
    assert envelope.has_more is False


def test_r45r_t22_truncated_false_stays_unsigned_or_complete():
    # Owner declaring ``truncated: false`` with total == items must
    # never be promoted to has_more=True — faithful, no invention.
    structured = {
        "data": {
            "total": 5,
            "items": [{"id": f"i-{i}"} for i in range(5)],
            "truncated": False,
        }
    }
    envelope = extract_pagination_envelope(structured)
    assert envelope is not None
    assert envelope.has_more is not True


# ---------------- R5 pagination negatives -----------------------------


def test_r5_n1_duplicate_page_does_not_inflate_collection():
    # Re-observing the same page adds nothing: union stays below the
    # declared total → never complete.
    assert not _coverage([
        _paged_attempt(_records(1, 40), 109),
        _paged_attempt(_records(1, 40), 109),
    ])


def test_r5_n2_duplicate_record_rejects_false_total():
    # Duplicate identity across pages ⇒ union < total → no fabricated
    # total from merged lengths.
    assert not _coverage([
        _paged_attempt(_records(1, 10), 15),
        _paged_attempt([{"id": 1}, *_records(11, 4)], 15),
    ])


def test_r5_n6_authoritative_total_conflict():
    # Contradictory declared totals ⇒ no authoritative total at all.
    assert not _coverage([
        _paged_attempt(_records(1, 40), 109),
        _paged_attempt(_records(41, 40), 99),
    ])


def test_r5_n7_missing_page_incomplete():
    # Union 69 < declared 109 → incomplete, period.
    assert not _coverage([
        _paged_attempt(_records(1, 40), 109),
        _paged_attempt(_records(81, 29), 109),
    ])


def test_r5_n8_truncated_walk_without_total_not_complete():
    # No declared total at all → unverifiable → never complete.
    assert not _coverage([
        _paged_attempt(_records(1, 40), None),
        _paged_attempt(_records(41, 40), None),
    ])


def test_r5_n9_budget_partial_honest():
    # A capped walk that collected 80 of 109 stays partial — the bound
    # is enforced by the governed loop; the evaluator only sees the
    # union.
    assert not _coverage([
        _paged_attempt(_records(1, 40), 109),
        _paged_attempt(_records(41, 40), 109),
    ])


def test_r5_positive_three_page_walk_109():
    """Sibling of live R5: 40+40+29 with stable total 109."""
    assert _coverage([
        _paged_attempt(_records(1, 40), 109),
        _paged_attempt(_records(41, 40), 109),
        _paged_attempt(_records(81, 29), 109),
    ])


def test_r5_n10_enumeration_not_satisfied_by_aggregate_total_alone():
    """Authoritative total alone does not prove enumeration delivery."""
    # The enumeration obligation requires the record union — an attempt
    # that only reports a total without items cannot satisfy it.
    assert not _coverage([_paged_attempt([], 109)])
