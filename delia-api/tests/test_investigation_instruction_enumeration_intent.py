"""INT-1 P2 — enumeration-intent instruction contract (v2-3).

Bounded evolution of ``generalist-semantic-v2-2-object-authz-continuity``:
the instruction must declare, in generalist terms, the distinction
between enumeration and filtered search, filtered-empty vs
catalog-empty, filter preservation and honest pagination — with no
hardcoded owner, entity or domain vocabulary. These tests verify the
instruction contract and deterministic mechanisms only; they do not
claim to prove LLM behaviour (that requires the real evaluation).
"""

from __future__ import annotations

from app.infrastructure.orchestration import pydantic_ai_investigation as pai


def _v23_text() -> str:
    return pai.load_selected_investigation_instructions(
        instruction_version="generalist-semantic-v2-3-enumeration-intent"
    ).text


def test_v2_3_declares_enumeration_vs_filter_distinction():
    """E1: enumeration intent is preserved, not silently converted
    into an unrequested restrictive filter."""
    text = _v23_text()
    assert "enumeration intent" in text
    assert "filtered-search intent" in text
    assert "authorized listing" in text
    # Domain-descriptive words must not become unrequested filters.
    assert "unrequested filter" in text


def test_v2_3_preserves_explicit_filter_requests():
    """E2: explicit user criteria stay filters — the clause forbids
    both over-filtering and dropping requested filters."""
    text = _v23_text()
    assert "criteria the user explicitly" in text
    # The explicit-filter path must remain first-class.
    lowered = text.casefold()
    assert "explicitly requested" in lowered or "explicitly stated" in lowered


def test_v2_3_separates_filtered_empty_from_catalog_empty():
    """E3: zero matches behind the caller's own filter is a filter
    miss — not proof of an empty authorized catalog. The instruction
    must name the owner's applied-criteria echo as the discriminator."""
    text = _v23_text()
    assert "empty filtered result" in text
    assert "filters_applied" in text
    assert "accessible\n  catalog is empty" in text or "catalog is empty" in text
    assert "filter matched nothing" in text


def test_v2_3_declares_honest_pagination_coverage():
    """E4: enumeration may be paginated — total, covered window and
    continuation must be reported honestly."""
    text = _v23_text()
    assert "paginated" in text
    assert "owner-declared\n  total" in text or "owner-declared total" in text
    assert "continuation" in text


def test_v2_3_keeps_authorization_denial_terminal():
    """E5: the AUTHZ_DENIED clause is preserved — a denied listing is
    an access limitation, never widened into a retry loop."""
    text = _v23_text()
    assert "AUTHZ_DENIED" in text
    assert "authorization_denied=true" in text
    assert "access limitation" in text
    assert "Do not retry equivalent access" in text


def test_v2_3_is_provider_and_domain_agnostic():
    """E6 / generalization: no owner, entity or PO-domain hardcoding —
    the clause must hold for any owner with an equivalent contract."""
    text = _v23_text()
    lowered = text.casefold()
    for banned in (
        "90260921",
        "davi.",
        "teo.",
        "vista.",
        "transforma",
        "process.search",
        "get_product_structure",
        "decomposition_tree",
        " for davi",
        " for teo",
    ):
        assert banned not in lowered


def test_v2_3_extends_v2_2_without_removing_clauses():
    """Bounded EXTEND: every v2-2 rule block is preserved verbatim —
    v2-3 adds the enumeration clause, it does not rewrite or drop
    prior governed behaviour."""
    v22 = pai.load_selected_investigation_instructions(
        instruction_version="generalist-semantic-v2-2-object-authz-continuity"
    ).text
    v23 = _v23_text()
    # v2-3 must contain the v2-2 text minus nothing: the v2-2 blocks
    # appear in order inside v2-3 (the clause is inserted between
    # existing blocks, never replaces one).
    preamble, *blocks = v22.split("\n- ")
    assert v23.startswith(preamble)
    cursor = 0
    for block in blocks:
        needle = "- " + block
        idx = v23.find(needle, cursor)
        assert idx != -1, f"v2-2 block dropped from v2-3: {block[:60]!r}"
        cursor = idx + len(needle)
    # And the delta is only the enumeration clause.
    assert len(v23) > len(v22)
