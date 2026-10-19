"""R5 integrity rework — page completeness and count honesty (doc 43).

TASK: DELIA-C3-R45-PAGINATION-INTEGRITY-AND-PRODUCTION-SSH-VALIDATION-01

Locks unsafe edges from independent review:
- has_more=None never proves complete aggregate
- isolated page>1 with has_more=False is not the query total
- gaps/duplicates/failures/budget => unknown, never fabricated total
"""

from __future__ import annotations

from typing import Any

from app.application.capability_provision.paginated_result_semantics import (
    CountResolutionKind,
    PersonalTicketScope,
    UNKNOWN_TOTAL_MESSAGE,
    aggregate_paginated_pages,
    classify_personal_ticket_scope,
    extract_pagination_envelope,
    personal_scope_response,
    resolve_count_semantics,
)


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


def test_r45r_t01_no_has_more_no_total():
    envelope = extract_pagination_envelope(
        {"items": [{"id": 1}, {"id": 2}], "page": 1, "page_size": 2}
    )
    assert envelope is not None
    assert envelope.has_more is None
    resolution = resolve_count_semantics(envelope)
    assert resolution.total is None
    assert resolution.kind is CountResolutionKind.PAGE_SLICE_NOT_TOTAL

    agg = aggregate_paginated_pages(
        [{"items": [{"id": 1}, {"id": 2}], "page": 1, "page_size": 2}]
    )
    assert agg.complete is False
    assert agg.failure_reason == "unsigned_completeness"
    assert resolve_count_semantics(None, aggregation=agg).total is None


def test_r45r_t02_last_page_only():
    envelope = extract_pagination_envelope(
        _page(n=4, page=3, has_more=False, id_offset=20)
    )
    resolution = resolve_count_semantics(envelope)
    assert resolution.total is None
    assert resolution.kind is CountResolutionKind.PARTIAL_UNKNOWN
    assert UNKNOWN_TOTAL_MESSAGE in resolution.message


def test_r45r_t03_complete_two_page_walk():
    pages = [
        _page(page=1, n=10, has_more=True, id_offset=0),
        _page(page=2, n=10, has_more=False, id_offset=10),
    ]
    agg = aggregate_paginated_pages(pages)
    assert agg.complete is True
    assert agg.unique_count == 20
    assert resolve_count_semantics(None, aggregation=agg).total == 20


def test_r45r_t04_missing_intermediate_page():
    pages = [
        _page(page=1, n=10, has_more=True, id_offset=0),
        _page(page=3, n=5, has_more=False, id_offset=20),
    ]
    agg = aggregate_paginated_pages(pages)
    assert agg.failed is True
    assert agg.failure_reason == "missing_intermediate_page"
    assert agg.complete is False
    assert resolve_count_semantics(None, aggregation=agg).total is None


def test_r45r_t05_duplicate_page():
    pages = [
        _page(page=1, n=5, has_more=True, id_offset=0),
        _page(page=1, n=5, has_more=False, id_offset=100),
    ]
    agg = aggregate_paginated_pages(pages)
    assert agg.failed is True
    assert agg.failure_reason == "duplicate_page"
    assert resolve_count_semantics(None, aggregation=agg).total is None


def test_r45r_t06_duplicate_ticket_id():
    p2 = _page(page=2, n=5, has_more=False, id_offset=10)
    p2["items"][0]["id"] = 1
    agg = aggregate_paginated_pages(
        [_page(page=1, n=10, has_more=True, id_offset=0), p2]
    )
    assert agg.complete is False
    assert "1" in agg.duplicate_ids
    assert resolve_count_semantics(None, aggregation=agg).total is None


def test_r45r_t07_malformed_page():
    agg = aggregate_paginated_pages(
        [_page(page=1, has_more=True), {"not": "a page"}]
    )
    assert agg.failed is True
    assert agg.failure_reason == "malformed_page"


def test_r45r_t08_page_failure():
    agg = aggregate_paginated_pages(
        [_page(page=1, has_more=True), None]
    )
    assert agg.failed is True
    assert agg.failure_reason == "page_failure"
    assert resolve_count_semantics(None, aggregation=agg).total is None


def test_r45r_t09_max_pages_exceeded():
    pages = [
        _page(page=i, has_more=True, id_offset=(i - 1) * 10)
        for i in range(1, 6)
    ]
    agg = aggregate_paginated_pages(pages, max_pages=3)
    assert agg.pages_fetched == 3
    assert agg.complete is False
    assert agg.failure_reason == "max_pages_exceeded"


def test_r45r_t10_budget_exhausted_same_as_partial():
    # Orchestrator stops walk early; aggregation of partial pages must
    # remain incomplete when last has_more is still True.
    pages = [
        _page(page=1, has_more=True, id_offset=0),
        _page(page=2, has_more=True, id_offset=10),
    ]
    agg = aggregate_paginated_pages(pages)
    assert agg.complete is False
    assert resolve_count_semantics(None, aggregation=agg).kind is (
        CountResolutionKind.PARTIAL_UNKNOWN
    )


def test_r45r_t11_authoritative_total():
    envelope = extract_pagination_envelope(
        _page(n=10, page=1, has_more=True, total_count=47)
    )
    resolution = resolve_count_semantics(envelope)
    assert resolution.kind is CountResolutionKind.AUTHORITATIVE_TOTAL
    assert resolution.total == 47


def test_r45r_t12_authoritative_total_conflict():
    pages = [
        _page(page=1, n=10, has_more=True, total_count=47, id_offset=0),
        _page(page=2, n=10, has_more=False, total_count=50, id_offset=10),
    ]
    agg = aggregate_paginated_pages(pages)
    assert agg.failed is True
    assert agg.failure_reason == "authoritative_total_conflict"
    assert resolve_count_semantics(None, aggregation=agg).total is None


def test_r45r_t13_missing_stable_ids():
    pages = [
        _page(page=1, n=3, has_more=False, omit_ids=True),
    ]
    agg = aggregate_paginated_pages(pages)
    assert agg.complete is False
    assert agg.failure_reason == "missing_stable_ids"
    assert resolve_count_semantics(None, aggregation=agg).total is None


def test_r45r_t14_filter_consistency_status_preserved():
    payload = _page(n=2, page=1, has_more=False)
    for item in payload["items"]:
        item["status"] = "open"
    envelope = extract_pagination_envelope(payload)
    resolution = resolve_count_semantics(envelope)
    assert resolution.total == 2
    assert all(i["status"] == "open" for i in envelope.items)


def test_r45r_t15_concurrent_mutation_via_duplicate_overlap():
    # Concurrent set change that reintroduces ids across pages ⇒ unknown.
    p2 = _page(page=2, n=10, has_more=False, id_offset=5)
    agg = aggregate_paginated_pages(
        [_page(page=1, n=10, has_more=True, id_offset=0), p2]
    )
    assert agg.complete is False
    assert agg.duplicate_ids
    assert resolve_count_semantics(None, aggregation=agg).total is None


def test_r45r_t16_personal_scope_protection():
    assert (
        classify_personal_ticket_scope("Quantos chamados tem para mim?")
        is PersonalTicketScope.MY_TICKETS_AMBIGUOUS
    )
    text = personal_scope_response(PersonalTicketScope.MY_TICKETS_AMBIGUOUS)
    assert text
    assert "10" not in text


def test_r45r_t17_unrelated_paginated_domain():
    # Generic product list envelope must not become personal ticket total.
    payload = {
        "items": [{"id": "p1"}, {"id": "p2"}],
        "page": 1,
        "page_size": 2,
        "has_more": False,
    }
    envelope = extract_pagination_envelope(payload)
    resolution = resolve_count_semantics(envelope)
    assert resolution.total == 2
    assert (
        classify_personal_ticket_scope("liste produtos da página")
        is PersonalTicketScope.NOT_APPLICABLE
    )


def test_r45r_t18_no_material_act():
    assert "ACT" not in UNKNOWN_TOTAL_MESSAGE
    assert personal_scope_response(PersonalTicketScope.ASSIGNED_TO_ME)
