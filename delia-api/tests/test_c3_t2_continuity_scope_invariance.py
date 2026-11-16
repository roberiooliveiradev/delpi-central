"""C3/T2 — investigation continuity & material-scope invariance.

TASK: DELIA-C3-T2-CENTRALIZED-INVESTIGATION-CONTINUITY-AND-SCOPE-INVARIANCE-01

Live reproduction (eval `or-qwen14b-a7b1dfa635af`): INT2_A and INT2_E
requested an unfiltered process enumeration. Page 1 was invoked WITHOUT
the ``params`` container; pages 2/3 carried ``params`` with ONLY window
selectors (``page``/``page_size``). ``_strip_window_args`` removed the
selectors but left an empty ``params`` mapping behind, so
``_invocation_scope`` digests diverged and ``_joint_collection_coverage``
grouped the pages separately → honest but wrong INCONCLUSIVE.

Contract: a continuation may alter ONLY proven window arguments; a
container that carried exclusively window selectors leaves no material
scope residue once stripped. Originally-empty containers, material
filters, owners, capabilities and nested business fields named like
window keys remain divergent — fail-closed.
"""

from __future__ import annotations

from app.application.capability_provision.semantic_capability_support import (
    OBLIGATION_INCONCLUSIVE,
    OBLIGATION_SATISFIED,
    _invocation_scope,
    _obligation_item,
    _required_scope_pairs,
)
from tests.test_c3_t2_final_gates_sufficiency_collection_multiturn import (
    _coverage,
    _teo_process_page,
)


def _enum_ob():
    return _obligation_item(
        {
            "description": "list processes",
            "evidence_source": "process",
            "operation": "read",
        }
    )


def _proc_items(start: int, end: int) -> list:
    return [{"code": f"PROC-{i:04d}"} for i in range(start, end)]


# -------------------------------------------------------------------
# RED — the live INT2_A / INT2_E divergence
# -------------------------------------------------------------------


def test_c01_window_only_container_pages_form_one_query():
    """C01/C03 — INT2_A reproduction: page 1 without ``params`` + pages
    2/3 whose ``params`` carry ONLY window selectors = ONE logical
    query → joint coverage SATISFIED."""
    obligation = _enum_ob()
    page1 = _teo_process_page(
        items=_proc_items(0, 40),
        total=109,
        args={"entity": "process", "action": "search"},
    )
    page2 = _teo_process_page(
        items=_proc_items(40, 80),
        total=109,
        args={
            "entity": "process",
            "action": "search",
            "params": {"page": 2, "page_size": 40},
        },
    )
    page3 = _teo_process_page(
        items=_proc_items(80, 109),
        total=109,
        args={
            "entity": "process",
            "action": "search",
            "params": {"page": 3, "page_size": 40},
        },
    )
    coverage = _coverage(
        (obligation,), (page1, page2, page3), delivery="enumeration"
    )
    assert coverage[obligation.description] == OBLIGATION_SATISFIED


def test_c03_window_only_container_scope_identity():
    """C03 — absent container ≡ container that held only window keys."""
    bare = _invocation_scope({"entity": "process", "action": "search"})
    windowed = _invocation_scope(
        {
            "entity": "process",
            "action": "search",
            "params": {"page": 2, "page_size": 40},
        }
    )
    assert bare == windowed


def test_c05_window_selector_variants_same_identity():
    """C05 — different legitimate window mechanisms (numeric page vs
    offset/limit vs cursor) all strip to the same material identity."""
    bare = _invocation_scope({"entity": "process", "action": "search"})
    for args in (
        {"entity": "process", "action": "search", "params": {"page": 2}},
        {
            "entity": "process",
            "action": "search",
            "params": {"offset": 40, "limit": 40},
        },
        {
            "entity": "process",
            "action": "search",
            "pagination": {"cursor": "abc123"},
        },
    ):
        assert _invocation_scope(args) == bare


def test_c14_material_filter_change_mid_sequence_never_united():
    """C14/C02 — page 1 unfiltered vs page 2+ filtered IS a material
    divergence: never united, stays honest."""
    obligation = _enum_ob()
    page1 = _teo_process_page(
        items=_proc_items(0, 60),
        total=109,
        args={"entity": "process", "action": "search"},
    )
    page2 = _teo_process_page(
        items=_proc_items(60, 109),
        total=109,
        args={
            "entity": "process",
            "action": "search",
            "params": {"status": "ativo"},
        },
    )
    coverage = _coverage(
        (obligation,), (page1, page2), delivery="enumeration"
    )
    assert coverage[obligation.description] != OBLIGATION_SATISFIED


# -------------------------------------------------------------------
# Guards — invariance boundaries that must remain divergent
# -------------------------------------------------------------------


def test_c06_nested_business_page_field_is_material():
    """C06 — a key named ``page`` two levels deep is a business field,
    not a proven window selector → remains in scope identity."""
    a = _invocation_scope(
        {"entity": "process", "params": {"criteria": {"page": "home"}}}
    )
    b = _invocation_scope(
        {"entity": "process", "params": {"criteria": {"page": "away"}}}
    )
    assert a != b
    assert any("page=home" in token for token in a)


def test_c07_empty_container_zero_args_structural():
    """Case A — an explicitly empty ``params`` carries ZERO leaf
    arguments: owner contracts treat it identically to absent params
    (TÉO live: page 1 invoked ``params:{}`` returned the unfiltered
    window). Structural difference only → same scope identity. Nested
    containers emptied recursively behave the same."""
    bare = _invocation_scope({"entity": "process", "action": "search"})
    emptied = _invocation_scope(
        {"entity": "process", "action": "search", "params": {}}
    )
    nested_empty = _invocation_scope(
        {"entity": "process", "action": "search", "meta": {"filters": {}}}
    )
    assert bare == emptied == nested_empty


def test_c07b_int2_r5_originally_empty_params_union():
    """INT2_R5 live shape: page 1 invoked ``params:{}`` + pages 2/3
    ``params:{page:N}`` → one query → coverage proven → SATISFIED."""
    obligation = _enum_ob()
    page1 = _teo_process_page(
        items=_proc_items(0, 40),
        total=109,
        args={"entity": "process", "action": "search", "params": {}},
    )
    page2 = _teo_process_page(
        items=_proc_items(40, 80),
        total=109,
        args={
            "entity": "process",
            "action": "search",
            "params": {"page": 2},
        },
    )
    page3 = _teo_process_page(
        items=_proc_items(80, 109),
        total=109,
        args={
            "entity": "process",
            "action": "search",
            "params": {"page": 3},
        },
    )
    coverage = _coverage(
        (obligation,), (page1, page2, page3), delivery="enumeration"
    )
    assert coverage[obligation.description] == OBLIGATION_SATISFIED


def test_declared_empty_container_marker_preserved():
    """Declared ``required_args {params:{}}`` keeps the exact-domain
    container marker — declared-unfiltered still rejects injected
    material filters."""
    tokens = _required_scope_pairs({"params": {}})
    assert "__container__=params" in tokens


def test_declared_window_only_required_args_no_material_marker():
    """Declared ``required_args {params:{page:2}}`` holds only window
    control → no material container requirement survives."""
    tokens = _required_scope_pairs({"params": {"page": 2}})
    assert "__container__=params" not in tokens


def test_c10_duplicate_pages_no_false_complete():
    """C10 — re-reading the same page cannot manufacture coverage."""
    obligation = _enum_ob()
    page1 = _teo_process_page(
        items=_proc_items(0, 40),
        total=109,
        args={"entity": "process", "action": "search"},
    )
    page1_again = _teo_process_page(
        items=_proc_items(0, 40),
        total=109,
        args={
            "entity": "process",
            "action": "search",
            "params": {"page": 2, "page_size": 40},
        },
    )
    coverage = _coverage(
        (obligation,), (page1, page1_again), delivery="enumeration"
    )
    assert coverage[obligation.description] != OBLIGATION_SATISFIED


def test_c11_inconsistent_owner_total_never_complete():
    """C11 — divergent declared totals = divergent queries, never one
    complete collection."""
    obligation = _enum_ob()
    page1 = _teo_process_page(
        items=_proc_items(0, 40),
        total=109,
        args={"entity": "process", "action": "search"},
    )
    page2 = _teo_process_page(
        items=_proc_items(40, 109),
        total=110,
        args={
            "entity": "process",
            "action": "search",
            "params": {"page": 2, "page_size": 40},
        },
    )
    coverage = _coverage(
        (obligation,), (page1, page2), delivery="enumeration"
    )
    assert coverage[obligation.description] != OBLIGATION_SATISFIED


def test_c12_incomplete_window_stays_inconclusive():
    """C12 — window-only equivalent pages that do not reach the owner
    total remain INCONCLUSIVE, not SATISFIED."""
    obligation = _enum_ob()
    page1 = _teo_process_page(
        items=_proc_items(0, 40),
        total=109,
        args={"entity": "process", "action": "search"},
    )
    page2 = _teo_process_page(
        items=_proc_items(40, 80),
        total=109,
        args={
            "entity": "process",
            "action": "search",
            "params": {"page": 2, "page_size": 40},
        },
    )
    coverage = _coverage(
        (obligation,), (page1, page2), delivery="enumeration"
    )
    assert coverage[obligation.description] == OBLIGATION_INCONCLUSIVE


def test_d01_declared_empty_container_tokens():
    """INT2_A declaration: ``required_args {params:{}}`` canonicalizes to
    the exact-domain marker only — a whole-map opaque leaf would be
    unprovable by every leaf-structured invocation."""
    tokens = _required_scope_pairs({"params": {}})
    assert tokens == ("__container__=params",)


def test_d02_declared_empty_container_provability():
    """Declared ``params:{}`` = 'params domain must be empty': satisfied
    by no-params and by window-only-params invocations alike."""
    from app.application.capability_provision.semantic_capability_support import (
        _required_scope_state,
    )

    required = _required_scope_pairs({"params": {}})
    bare = _invocation_scope({"entity": "process", "action": "search"})
    windowed = _invocation_scope(
        {
            "entity": "process",
            "action": "search",
            "params": {"page": 2, "page_size": 40},
        }
    )
    assert _required_scope_state(required, bare) == "ok"
    assert _required_scope_state(required, windowed) == "ok"


def test_d03_declared_empty_container_still_blocks_material_filter():
    """Fail-closed sibling: declared ``params:{}`` must NOT accept an
    invocation carrying a material filter leaf."""
    from app.application.capability_provision.semantic_capability_support import (
        _required_scope_state,
    )

    required = _required_scope_pairs({"params": {}})
    filtered = _invocation_scope(
        {
            "entity": "process",
            "action": "search",
            "params": {"status": "inativo"},
        }
    )
    assert _required_scope_state(required, filtered) == "unproven"


def test_d04_int2_a_end_to_end_declared_empty_multipage_union():
    """INT2_A full reproduction: obligation declared ``params:{}`` +
    page1 without params + pages 2/3 window-only → one query, coverage
    proven → SATISFIED."""
    obligation = _obligation_item(
        {
            "description": "list processes",
            "evidence_source": "process",
            "operation": "read",
            "required_args": {
                "entity": "process",
                "action": "search",
                "params": {},
            },
        }
    )
    page1 = _teo_process_page(
        items=_proc_items(0, 40),
        total=109,
        args={"entity": "process", "action": "search"},
    )
    page2 = _teo_process_page(
        items=_proc_items(40, 80),
        total=109,
        args={
            "entity": "process",
            "action": "search",
            "params": {"page": 2, "page_size": 40},
        },
    )
    page3 = _teo_process_page(
        items=_proc_items(80, 109),
        total=109,
        args={
            "entity": "process",
            "action": "search",
            "params": {"page": 3, "page_size": 40},
        },
    )
    coverage = _coverage(
        (obligation,), (page1, page2, page3), delivery="enumeration"
    )
    assert coverage[obligation.description] == OBLIGATION_SATISFIED
