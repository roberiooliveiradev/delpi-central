"""C3/T2 final gates — sufficiency anchors, R5-N3/N4/N5, R6 roles.

TASK: DELIA-C3-T2-SUFFICIENCY-COLLECTION-INTEGRITY-AND-MULTITURN-FINAL-GATES-01

WS-1: presentation-class anchors (summary/analysis) must not veto an
authoritative READ aggregate under matching material filters; negatives
S4–S10 remain fail-closed.

WS-2: collection identity is owned by ``_joint_collection_coverage``
(same owner + same invocation scope). R5-N3/N4/N5 contract proofs.

WS-3: prior_turns blob authorizes only user-role content for invented
identifier gating.
"""

from __future__ import annotations

from app.application.capability_provision.semantic_capability_support import (
    OBLIGATION_INCONCLUSIVE,
    OBLIGATION_SATISFIED,
    OBLIGATION_UNSATISFIED,
    _evaluate_material_obligations,
    _invocation_scope,
    _obligation_item,
)
from app.application.model_invocation.contracts import (
    ConversationContextTurn,
    TurnKind,
)
from app.infrastructure.orchestration.pydantic_ai_investigation import (
    invented_record_tokens,
)
from tests.test_rc5_anchor_correctness_remediation import _attempt


def _coverage(obligations, business, delivery=None):
    kwargs = {"obligations": obligations, "business": business}
    if delivery is not None:
        kwargs["delivery"] = delivery
    return dict(_evaluate_material_obligations(**kwargs))


def _agg_ob(
    *,
    desc: str = "count active transformation processes",
    source: str = "summary",
    operation: str = "analysis",
    required_args: dict | None = None,
):
    if required_args is None:
        required_args = {
            "params": {"status": "ativo"},
            "view": "summary",
        }
    return _obligation_item(
        {
            "description": desc,
            "evidence_source": source,
            "operation": operation,
            "required_args": required_args,
        }
    )


def _teo_process_page(
    *,
    items: list | None = None,
    total: int = 109,
    args: dict | None = None,
    specialist: str = "teo",
    remote: str = "teo.read",
    operation_class: str = "READ",
):
    if args is None:
        args = {
            "entity": "process",
            "action": "search",
            "params": {"status": "ativo"},
        }
    if items is None:
        items = [{"code": f"PROC-{i:04d}"} for i in range(min(40, total))]
    return _attempt(
        entity="process",
        capability="teo.read",
        vocabulary=("process", "search"),
        items=items,
        total=total,
        specialist=specialist,
        remote=remote,
        operation_class=operation_class,
        scope=_invocation_scope(args),
        content=f"total_count={total}",
    )


# -------------------------------------------------------------------
# WS-1 — sufficiency / presentation anchors (S1–S10)
# -------------------------------------------------------------------


def test_s1_g2_presentation_anchor_satisfied_by_teo_read_total():
    """S1 — summary/analysis plan + teo.read total under status=ativo."""
    obligation = _agg_ob()
    attempt = _teo_process_page(total=109)
    coverage = _coverage((obligation,), (attempt,), delivery="aggregation")
    assert coverage[obligation.description] == OBLIGATION_SATISFIED


def test_s2_params_vs_arguments_leaf_equivalence():
    """S2 — params.code ↔ arguments.code when leaf values match."""
    obligation = _obligation_item(
        {
            "description": "product structure 90260921",
            "evidence_source": "product",
            "operation": "read",
            "required_args": {"params": {"code": "90260921"}},
        }
    )
    attempt = _attempt(
        entity="product",
        vocabulary=("product", "structure"),
        identity=("90260921",),
        items=[{"code": "90260921", "levels": 3}],
        total=1,
        specialist="davi",
        remote="davi.read",
        operation_class="READ",
        scope=_invocation_scope(
            {"entity": "product", "arguments": {"code": "90260921"}}
        ),
        content="structure ok",
    )
    coverage = _coverage((obligation,), (attempt,), delivery="enumeration")
    assert coverage[obligation.description] == OBLIGATION_SATISFIED


def test_s3_capability_read_satisfies_analysis_presentation_anchor():
    """S3 — READ capability demonstrates analysis-anchored aggregation."""
    obligation = _agg_ob(operation="analysis")
    attempt = _teo_process_page(operation_class="READ")
    coverage = _coverage((obligation,), (attempt,), delivery="aggregation")
    assert coverage[obligation.description] == OBLIGATION_SATISFIED


def test_s4_missing_status_filter_not_satisfied():
    """S4 — unfiltered search cannot satisfy status=ativo aggregation."""
    obligation = _agg_ob()
    attempt = _teo_process_page(
        args={"entity": "process", "action": "search", "params": {}},
    )
    coverage = _coverage((obligation,), (attempt,), delivery="aggregation")
    assert coverage[obligation.description] != OBLIGATION_SATISFIED


def test_s5_mention_only_not_satisfied():
    """S5 — text that merely mentions processes is not a metric."""
    obligation = _agg_ob()
    attempt = _attempt(
        entity="process",
        vocabulary=("process",),
        items=[],
        total=None,
        structured={
            "capability": "teo.read",
            "entity": "process",
            "shape": "note",
            "data": {"note": "there are processes"},
        },
        content="there are processes",
        specialist="teo",
        remote="teo.read",
        operation_class="READ",
        scope=_invocation_scope(
            {
                "entity": "process",
                "action": "search",
                "params": {"status": "ativo"},
            }
        ),
    )
    coverage = _coverage((obligation,), (attempt,), delivery="aggregation")
    assert coverage[obligation.description] != OBLIGATION_SATISFIED


def test_s6_partial_page_without_total_not_aggregation_satisfied():
    """S6 — 40 items without authoritative total ≠ complete count."""
    obligation = _agg_ob()
    attempt = _attempt(
        entity="process",
        vocabulary=("process", "search"),
        structured={
            "capability": "teo.read",
            "entity": "process",
            "shape": "paged_list",
            "data": {
                "items": [
                    {"code": f"PROC-{i:04d}"} for i in range(40)
                ],
                "is_complete": False,
                "truncated": True,
            },
        },
        specialist="teo",
        remote="teo.read",
        operation_class="READ",
        scope=_invocation_scope(
            {
                "entity": "process",
                "action": "search",
                "params": {"status": "ativo"},
            }
        ),
        content="page window",
    )
    coverage = _coverage((obligation,), (attempt,), delivery="aggregation")
    assert coverage[obligation.description] != OBLIGATION_SATISFIED


def test_s6b_authoritative_total_sufficient_for_quantity_question():
    """S6b — quantity-only: owner total under filter is enough."""
    obligation = _agg_ob()
    attempt = _teo_process_page(
        items=[{"code": f"PROC-{i:04d}"} for i in range(40)],
        total=109,
    )
    coverage = _coverage((obligation,), (attempt,), delivery="aggregation")
    assert coverage[obligation.description] == OBLIGATION_SATISFIED


def test_s7_different_owner_does_not_satisfy():
    """S7 — foreign-owner evidence does not satisfy TEO-scoped plan
    when entity vocabulary mismatches presentation but owner kind differs
    materially (no process vocabulary)."""
    obligation = _agg_ob(source="process", operation="read")
    attempt = _attempt(
        entity="ticket",
        vocabulary=("ticket", "search"),
        items=[{"id": 1}],
        total=109,
        specialist="other",
        remote="other.read",
        operation_class="READ",
        scope=_invocation_scope(
            {
                "entity": "ticket",
                "action": "search",
                "params": {"status": "ativo"},
            }
        ),
        content="tickets=109",
    )
    coverage = _coverage((obligation,), (attempt,), delivery="aggregation")
    assert coverage[obligation.description] == OBLIGATION_UNSATISFIED


def test_s8_wrong_product_identifier_rejected():
    """S8 — different product code never satisfies the obligated one."""
    obligation = _obligation_item(
        {
            "description": "structure of product 90260921",
            "evidence_source": "product",
            "operation": "read",
            "required_args": {"arguments": {"code": "90260921"}},
        }
    )
    attempt = _attempt(
        entity="product",
        vocabulary=("product", "structure"),
        identity=("11111111",),
        items=[{"code": "11111111"}],
        total=1,
        specialist="davi",
        remote="davi.read",
        operation_class="READ",
        scope=_invocation_scope(
            {"entity": "product", "arguments": {"code": "11111111"}}
        ),
        content="other product",
    )
    coverage = _coverage((obligation,), (attempt,), delivery="enumeration")
    assert coverage[obligation.description] == OBLIGATION_UNSATISFIED


def test_s9_one_satisfied_does_not_mask_pending():
    """S9 — satisfied obligation must not mask a second pending one."""
    count_ob = _agg_ob(desc="count active processes")
    structure_ob = _obligation_item(
        {
            "description": "structure of product 90260921",
            "evidence_source": "product",
            "operation": "read",
            "required_args": {"arguments": {"code": "90260921"}},
        }
    )
    attempt = _teo_process_page(total=109)
    coverage = _coverage(
        (count_ob, structure_ob),
        (attempt,),
        delivery="aggregation",
    )
    assert coverage[count_ob.description] == OBLIGATION_SATISFIED
    assert coverage[structure_ob.description] != OBLIGATION_SATISFIED


def test_s10_grounded_insufficient_stays_inconclusive_not_complete():
    """S10 — grounded but incomplete enumeration stays INCONCLUSIVE."""
    obligation = _obligation_item(
        {
            "description": "list active processes",
            "evidence_source": "process",
            "operation": "read",
            "required_args": {"params": {"status": "ativo"}},
        }
    )
    attempt = _teo_process_page(
        items=[{"code": f"PROC-{i:04d}"} for i in range(40)],
        total=109,
    )
    coverage = _coverage(
        (obligation,), (attempt,), delivery="enumeration"
    )
    assert coverage[obligation.description] == OBLIGATION_INCONCLUSIVE


# -------------------------------------------------------------------
# WS-2 — R5-N3 / N4 / N5 via joint collection coverage
# -------------------------------------------------------------------


def _enum_ob():
    return _obligation_item(
        {
            "description": "list active processes",
            "evidence_source": "process",
            "required_args": {"params": {"status": "ativo"}},
        }
    )


def test_r5_n3_cross_owner_pages_not_united():
    """R5-N3 — structurally similar pages from different owners ≠ one
    authoritative collection."""
    obligation = _enum_ob()
    args = {
        "entity": "process",
        "action": "search",
        "params": {"status": "ativo"},
    }
    page_a = _teo_process_page(
        items=[{"code": f"A-{i:04d}"} for i in range(60)],
        total=109,
        specialist="teo",
        remote="teo.read",
        args=args,
    )
    page_b = _teo_process_page(
        items=[{"code": f"B-{i:04d}"} for i in range(49)],
        total=109,
        specialist="other-owner",
        remote="other.read",
        args=args,
    )
    coverage = _coverage(
        (obligation,), (page_a, page_b), delivery="enumeration"
    )
    assert coverage[obligation.description] != OBLIGATION_SATISFIED


def test_r5_n4_divergent_filters_not_united():
    """R5-N4 — status=ativo then status=inativo ≠ complete active set."""
    obligation = _enum_ob()
    active = {
        "entity": "process",
        "action": "search",
        "params": {"status": "ativo"},
    }
    inactive = {
        "entity": "process",
        "action": "search",
        "params": {"status": "inativo"},
    }
    page1 = _teo_process_page(
        items=[{"code": f"A-{i:04d}"} for i in range(60)],
        total=109,
        args=active,
    )
    page2 = _teo_process_page(
        items=[{"code": f"I-{i:04d}"} for i in range(49)],
        total=109,
        args=inactive,
    )
    coverage = _coverage(
        (obligation,), (page1, page2), delivery="enumeration"
    )
    assert coverage[obligation.description] != OBLIGATION_SATISFIED


def test_r5_n5_divergent_authz_scope_not_united():
    """R5-N5 — incompatible authorization scopes never form one set."""
    obligation = _obligation_item(
        {
            "description": "list active processes unit 01",
            "evidence_source": "process",
            "required_args": {
                "params": {"status": "ativo", "filial_id": "01"},
            },
        }
    )
    scope_01 = {
        "entity": "process",
        "action": "search",
        "params": {"status": "ativo", "filial_id": "01"},
    }
    scope_02 = {
        "entity": "process",
        "action": "search",
        "params": {"status": "ativo", "filial_id": "02"},
    }
    page1 = _teo_process_page(
        items=[{"code": f"U1-{i:04d}"} for i in range(60)],
        total=109,
        args=scope_01,
    )
    page2 = _teo_process_page(
        items=[{"code": f"U2-{i:04d}"} for i in range(49)],
        total=109,
        args=scope_02,
    )
    coverage = _coverage(
        (obligation,), (page1, page2), delivery="enumeration"
    )
    assert coverage[obligation.description] != OBLIGATION_SATISFIED


def test_r5_positive_same_owner_filter_scope_union():
    """Positive multipage: same owner + filter + scope → SATISFIED."""
    obligation = _enum_ob()
    base = {
        "entity": "process",
        "action": "search",
        "params": {"status": "ativo"},
    }
    p2 = {
        "entity": "process",
        "action": "search",
        "params": {"status": "ativo", "page": 2},
    }
    p3 = {
        "entity": "process",
        "action": "search",
        "params": {"status": "ativo", "page": 3},
    }
    attempts = (
        _teo_process_page(
            items=[{"code": f"PROC-{i:04d}"} for i in range(40)],
            total=109,
            args=base,
        ),
        _teo_process_page(
            items=[{"code": f"PROC-{i:04d}"} for i in range(40, 80)],
            total=109,
            args=p2,
        ),
        _teo_process_page(
            items=[{"code": f"PROC-{i:04d}"} for i in range(80, 109)],
            total=109,
            args=p3,
        ),
    )
    coverage = _coverage((obligation,), attempts, delivery="enumeration")
    assert coverage[obligation.description] == OBLIGATION_SATISFIED


# -------------------------------------------------------------------
# WS-3 — prior_turns role filtering for invented identifiers
# -------------------------------------------------------------------


def test_r6_delia_result_invented_code_not_authorized():
    """DELIA_RESULT-named code must not authorize the same fabrication.

    Uses the real ``ConversationContextTurn`` contract (``kind``), not a
    fake ``role`` attribute that production never sets.
    """
    invented = invented_record_tokens(
        ["P12345"],
        input_text="pode continuar",
        prior_turns=(
            ConversationContextTurn(
                kind=TurnKind.USER_INPUT,
                content="Quero ver a estrutura de um produto.",
            ),
            ConversationContextTurn(
                kind=TurnKind.DELIA_RESULT,
                content="Vou consultar o produto P12345.",
            ),
        ),
    )
    assert invented == ["P12345"]


def test_r6_user_named_code_in_prior_turn_authorized():
    invented = invented_record_tokens(
        ["90260921"],
        input_text="pode continuar",
        prior_turns=(
            ConversationContextTurn(
                kind=TurnKind.USER_INPUT,
                content="Quero a estrutura do produto 90260921",
            ),
            ConversationContextTurn(
                kind=TurnKind.DELIA_RESULT,
                content="Consultando estrutura…",
            ),
        ),
    )
    assert invented == []


def test_r6_clarification_reply_in_input_authorizes():
    invented = invented_record_tokens(
        ["90260921"],
        input_text="90260921",
        prior_turns=(),
    )
    assert invented == []
