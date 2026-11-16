"""C3/T2 — INT3 anchor classification & demonstrable vocabulary.

TASK: DELIA-C3-T2-INT3-ANCHOR-CLASSIFICATION-AND-DEMONSTRABLE-VOCABULARY-01

Defect (residual INT3-OBLIGATION-DEMONSTRATION-DEPTH): presentation-class
``evidence_source`` anchors (e.g. ``display_format``) only bypassed the
owner-echo veto under ``delivery=aggregation``. Under ``record_detail`` /
``explanation`` / ``enumeration`` the same class of anchor locked real,
congruent business evidence into UNSATISFIED/INCONCLUSIVE even when the
obligation declared a mechanically checkable entity scope.

Fix under test: the presentation class (extended with display/format/
layout vocabulary) bypasses the echo veto under ANY delivery when the
attempt carries business evidence AND the declared ``required_scope``
entity tokens intersect the attempt's owner anchor tokens — while every
downstream gate (scope, operation, identity, collection completeness,
aggregation metric, ACT postcondition) remains unchanged.

Classes per RQ-3:
- A presentation: never owner business evidence; demonstration via
  congruent business evidence only.
- B business entity: exact echo only — no singularization.
- C selector/transport: dotted surfaces stay rejected at acceptance;
  owner-echoed capability selectors remain legitimate anchor vocabulary.
- D unknown/undemonstrable: honest non-SATISFIED, never invented.
"""

from __future__ import annotations

import dataclasses

from app.application.capability_provision.semantic_capability_support import (
    OBLIGATION_INCONCLUSIVE,
    OBLIGATION_SATISFIED,
    OBLIGATION_UNSATISFIED,
    _evaluate_material_obligations,
    _invocation_scope,
    _obligation_item,
)
from tests.test_rc5_anchor_correctness_remediation import _attempt


def _coverage(obligations, business, delivery=None):
    kwargs = {"obligations": obligations, "business": business}
    if delivery is not None:
        kwargs["delivery"] = delivery
    return dict(_evaluate_material_obligations(**kwargs))


def _presentation_ob(
    *,
    desc: str = "estrutura do produto 90260921",
    source: str = "display_format",
    operation: str = "read",
    required_args: dict | None = None,
):
    if required_args is None:
        required_args = {
            "entity": "product_structure",
            "params": {"code": "90260921"},
        }
    return _obligation_item(
        {
            "description": desc,
            "evidence_source": source,
            "operation": operation,
            "required_args": required_args,
        }
    )


def _davi_structure(
    *,
    data_complete: bool = True,
    truncated: bool = False,
    operation_class: str = "READ",
    entity: str = "product_structure",
    scope_entity: str = "product_structure",
    limitations: tuple = (),
):
    attempt = _attempt(
        entity=entity,
        capability="get_product_structure",
        vocabulary=("get_product_structure",),
        identity=("90260921",),
        specialist="davi",
        remote="davi.read",
        operation_class=operation_class,
        scope=_invocation_scope(
            {
                "entity": scope_entity,
                "capability": "get_product_structure",
                "params": {"code": "90260921"},
            }
        ),
        items=[{"code": "90260921", "components": [{"code": "C-1"}]}],
        total=1,
        data_complete=data_complete,
        truncated=truncated,
        content="21010421 CHICOTE DE LIGACAO",
    )
    if limitations:
        attempt = dataclasses.replace(attempt, limitations=limitations)
    return attempt


# -------------------------------------------------------------------
# RED — presentation anchors under non-aggregation deliveries
# -------------------------------------------------------------------


def test_int3_display_format_record_detail_satisfied():
    """G1/P3 regression: display_format anchor + record_detail delivery
    + congruent DAVI product_structure evidence → demonstrated."""
    obligation = _presentation_ob()
    attempt = _davi_structure()
    coverage = _coverage(
        (obligation,), (attempt,), delivery="record_detail"
    )
    assert coverage[obligation.description] == OBLIGATION_SATISFIED


def test_int3_display_format_explanation_satisfied():
    """Sibling delivery: explanation + congruent evidence → SATISFIED."""
    obligation = _presentation_ob()
    attempt = _davi_structure()
    coverage = _coverage((obligation,), (attempt,), delivery="explanation")
    assert coverage[obligation.description] == OBLIGATION_SATISFIED


def test_int3_display_format_enumeration_complete_satisfied():
    """Enumeration + presentation anchor + complete collection →
    SATISFIED (coverage gate still enforced, just satisfied)."""
    obligation = _presentation_ob(
        desc="lista de estruturas de produto",
        required_args={"entity": "product_structure"},
    )
    attempt = _attempt(
        entity="product_structure",
        capability="get_product_structure",
        vocabulary=("get_product_structure",),
        specialist="davi",
        remote="davi.read",
        operation_class="READ",
        scope=_invocation_scope({"entity": "product_structure"}),
        items=[{"code": "A"}, {"code": "B"}],
        total=2,
        content="2 items",
    )
    coverage = _coverage((obligation,), (attempt,), delivery="enumeration")
    assert coverage[obligation.description] == OBLIGATION_SATISFIED


def test_int3_summary_anchor_non_aggregation_satisfied():
    """The pre-existing presentation vocabulary (summary) must bypass
    the echo veto under non-aggregation deliveries too — the fix is
    class-wide, not display_format-specific."""
    obligation = _presentation_ob(source="summary")
    attempt = _davi_structure()
    coverage = _coverage(
        (obligation,), (attempt,), delivery="record_detail"
    )
    assert coverage[obligation.description] == OBLIGATION_SATISFIED


def test_int3_layout_anchor_record_detail_satisfied():
    """layout is delivery-surface vocabulary — same class as
    display_format."""
    obligation = _presentation_ob(source="layout")
    attempt = _davi_structure()
    coverage = _coverage(
        (obligation,), (attempt,), delivery="record_detail"
    )
    assert coverage[obligation.description] == OBLIGATION_SATISFIED


def test_int3_presentation_enumeration_incomplete_binds_inconclusive():
    """Presentation anchor + enumeration + congruent but INCOMPLETE
    collection → bound, never demonstrated (coverage gate intact)."""
    obligation = _presentation_ob(
        desc="lista de estruturas de produto",
        required_args={"entity": "product_structure"},
    )
    attempt = _attempt(
        entity="product_structure",
        capability="get_product_structure",
        vocabulary=("get_product_structure",),
        specialist="davi",
        remote="davi.read",
        operation_class="READ",
        scope=_invocation_scope({"entity": "product_structure"}),
        items=[{"code": "A"}],
        total=5,
        data_complete=False,
        truncated=True,
        content="partial",
    )
    coverage = _coverage((obligation,), (attempt,), delivery="enumeration")
    assert coverage[obligation.description] == OBLIGATION_INCONCLUSIVE


# -------------------------------------------------------------------
# Negative guards — the class relaxation must never widen SATISFIED
# -------------------------------------------------------------------


def test_int3_presentation_wrong_entity_never_satisfied():
    """Declared entity=sales_order vs echoed product_structure —
    congruence fails → never satisfied."""
    obligation = _presentation_ob(
        required_args={"entity": "sales_order"}
    )
    attempt = _davi_structure(scope_entity="sales_order")
    coverage = _coverage(
        (obligation,), (attempt,), delivery="record_detail"
    )
    assert coverage[obligation.description] != OBLIGATION_SATISFIED


def test_int3_presentation_without_entity_scope_never_satisfied():
    """No declared entity tokens → congruence cannot be proven →
    never satisfied (same fail-closed rule as aggregation S2b)."""
    obligation = _presentation_ob(
        required_args={"params": {"code": "90260921"}}
    )
    attempt = _davi_structure()
    coverage = _coverage(
        (obligation,), (attempt,), delivery="record_detail"
    )
    assert coverage[obligation.description] != OBLIGATION_SATISFIED


def test_int3_presentation_read_never_demonstrates_act():
    """READ evidence never satisfies an ACT obligation — presentation
    bypass does not relax the operation/postcondition gate."""
    obligation = _presentation_ob(operation="act")
    attempt = _davi_structure()
    coverage = _coverage(
        (obligation,), (attempt,), delivery="record_detail"
    )
    assert coverage[obligation.description] != OBLIGATION_SATISFIED


def test_int3_presentation_non_business_evidence_never_satisfied():
    """Discovery-metadata-only observation is not business evidence —
    the presentation path requires real business evidence."""
    obligation = _presentation_ob()
    attempt = _davi_structure(
        limitations=("discovery_metadata_observation",)
    )
    coverage = _coverage(
        (obligation,), (attempt,), delivery="record_detail"
    )
    assert coverage[obligation.description] != OBLIGATION_SATISFIED


def test_int3_entity_plural_no_singularization():
    """Class B: ``processes`` is NOT the ``process`` owner token —
    exact matching only, no derived equivalence (even with
    entity=process declared in scope)."""
    obligation = _obligation_item(
        {
            "description": "lista de processos",
            "evidence_source": "processes",
            "operation": "read",
            "required_args": {"entity": "process"},
        }
    )
    attempt = _attempt(
        entity="process",
        capability="teo.read",
        vocabulary=("process", "search"),
        specialist="teo",
        remote="teo.read",
        operation_class="READ",
        scope=_invocation_scope({"entity": "process"}),
        items=[{"code": "PROC-1"}],
        total=1,
    )
    coverage = _coverage((obligation,), (attempt,), delivery="enumeration")
    assert coverage[obligation.description] != OBLIGATION_SATISFIED


def test_int3_unknown_anchor_wrong_owner_vocabulary_disproven():
    """Class D: ``transportadora`` anchor vs owner echo of a different
    kind — the echoed vocabulary disproves the bind outright."""
    obligation = _obligation_item(
        {
            "description": "lista de transportadoras",
            "evidence_source": "transportadora",
            "operation": "read",
            "required_args": {"entity": "carrier"},
        }
    )
    attempt = _attempt(
        entity="product_structure",
        capability="get_product_structure",
        vocabulary=("get_product_structure",),
        specialist="davi",
        remote="davi.read",
        operation_class="READ",
        scope=_invocation_scope({"entity": "carrier"}),
        items=[{"code": "C-1"}],
        total=1,
    )
    coverage = _coverage(
        (obligation,), (attempt,), delivery="enumeration"
    )
    assert coverage[obligation.description] == OBLIGATION_UNSATISFIED


def test_int3_entity_anchor_exact_echo_still_satisfied():
    """Class B positive regression: exact entity echo still demonstrates
    — the presentation path did not absorb business anchors."""
    obligation = _obligation_item(
        {
            "description": "estrutura do produto 90260921",
            "evidence_source": "product_structure",
            "operation": "read",
            "required_args": {
                "entity": "product_structure",
                "params": {"code": "90260921"},
            },
        }
    )
    attempt = _davi_structure()
    coverage = _coverage(
        (obligation,), (attempt,), delivery="record_detail"
    )
    assert coverage[obligation.description] == OBLIGATION_SATISFIED
