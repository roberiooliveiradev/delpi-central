"""C3/T2 evidence-closure negatives — G2 / REF05 / R5 / R6 / invented tokens.

Locks the independent-review matrix without inventing a second sufficiency
engine. Reuses canonical finalize / pagination / invented-token owners.
"""

from __future__ import annotations

import dataclasses

import pytest
from tests.support.native_mcp_fixtures import (
    alpha_beta_servers,
    native_toolset_stub,
)


@pytest.fixture(autouse=True)
def _native_toolsets_stub():
    with native_toolset_stub(alpha_beta_servers()):
        yield


from app.application.capability_provision.contracts import (
    InvestigationAnswer,
    InvestigationAnswerStatus,
)
from app.application.capability_provision.generic_evidence_renderer import (
    CountResolutionKind,
    aggregate_paginated_pages,
    resolve_count_semantics,
)
from app.application.capability_provision.semantic_capability_support import (
    OBLIGATION_SATISFIED,
    _apply_declared_answer,
    _evaluate_material_obligations,
    _finalize_agent_collected_attempts,
    _plan_delivery_mode,
)
from app.application.interaction.capability_attempt import (
    OWNER_PATH_UNBOUND,
    GovernedCapabilityAttempt,
    GovernedCapabilityStatus,
)
from app.application.interaction.turn_budget import TurnDeadline
from app.infrastructure.orchestration.pydantic_ai_investigation import (
    invented_record_tokens,
)
from tests.test_pydantic_ai_semantic_rework import (
    _gates,
    _read_plan,
    _success_attempt,
)


def _page(
    *,
    n: int = 10,
    page: int | None = 1,
    page_size: int = 10,
    has_more: bool | None = True,
    total_count: int | None = None,
    id_offset: int = 0,
) -> dict:
    items = [
        {"id": id_offset + i + 1, "title": f"T{id_offset + i + 1}"}
        for i in range(n)
    ]
    payload: dict = {"items": items, "page_size": page_size}
    if page is not None:
        payload["page"] = page
    if has_more is not None:
        payload["has_more"] = has_more
    if total_count is not None:
        payload["total_count"] = total_count
    return payload


# ---------------- G2 / false COMPLETE ---------------------------------


def test_g2_plan_absent_keeps_clarification_over_unrelated_evidence():
    """RQ-2/RQ-3: plan=None + clarification must stay ask-back."""
    gates = _gates()
    related = _success_attempt(
        content="unrelated aggregate",
        root="TEO-AGG-01",
        structured={"data": {"total": 7, "is_complete": True}},
    )
    result = _finalize_agent_collected_attempts(
        gates,
        input_text="Quero ver a estrutura de um produto.",
        collected=(related,),
        correlation="g2-plan-none",
        workspace_context=None,
        deadline=TurnDeadline.start(30.0),
        unbound_outcome=OWNER_PATH_UNBOUND,
        plan=None,
        clarification_question="Qual é o código do produto?",
    )
    assert result.status is GovernedCapabilityStatus.CLARIFICATION_REQUIRED
    assert "agent_requested_clarification" in result.limitations
    assert "Qual é o código" in (result.content or "")


def test_g2_one_satisfied_one_pending_does_not_publish_complete():
    """RQ-3: mixed obligation coverage must not promote COMPLETE."""
    from tests.test_int2_typed_objective_obligation_contract import (
        _anchored_attempt,
    )

    gates = _gates()
    plan = gates._accept_semantic_investigation_plan(
        goal_class="analyze",
        comparison_requested=False,
        target_identities=[],
        evidence_needed=[
            {
                "description": "Contagem de processos ativos",
                "evidence_source": "process",
            },
            {
                "description": "Estrutura do produto 90260921",
                "evidence_source": "product",
                "required_args": {"params": {"code": "90260921"}},
            },
        ],
        expected_delivery="aggregation",
        correlation="g2-mixed",
    )
    assert plan is not None
    hit = _anchored_attempt(
        root="PROC-0001",
        vocabulary=("process", "search"),
        structured={
            "success": True,
            "data": {
                "total": 109,
                "items": [{"codigo_processo": "PROC-0001"}],
                "is_complete": True,
            },
        },
    )
    coverage = _evaluate_material_obligations(
        obligations=plan.evidence_needed,
        business=(hit,),
        delivery=_plan_delivery_mode(plan),
    )
    states = {desc: state for desc, state in coverage}
    assert states.get("Contagem de processos ativos") == OBLIGATION_SATISFIED
    assert states.get("Estrutura do produto 90260921") != OBLIGATION_SATISFIED

    terminal = _finalize_agent_collected_attempts(
        gates,
        input_text="Quantos ativos e estrutura 90260921?",
        collected=(hit,),
        correlation="g2-mixed",
        workspace_context=None,
        deadline=TurnDeadline.start(30.0),
        unbound_outcome=OWNER_PATH_UNBOUND,
        plan=plan,
        clarification_question="Falta o código do produto?",
    )
    assert terminal.status is GovernedCapabilityStatus.CLARIFICATION_REQUIRED
    assert "agent_requested_clarification" in terminal.limitations

    declared = InvestigationAnswer(
        schema_version="1",
        status=InvestigationAnswerStatus.COMPLETE,
        answer="Tudo resolvido com 109 ativos.",
        evidence_refs=(0,),
    )
    out = _apply_declared_answer(
        terminal=terminal,
        declared_answer=declared,
        collected=(hit,),
        plan=plan,
        correlation="g2-mixed",
        unbound_outcome=None,
    )
    assert out.status is not GovernedCapabilityStatus.SUCCESS
    assert (
        "declared_status_overridden" in out.limitations
        or "agent_requested_clarification" in out.limitations
    )


def test_g2_complete_without_bound_evidence_is_overridden():
    """RQ-3: COMPLETE with empty/unbound refs cannot become FACT."""
    from tests.test_int2_typed_objective_obligation_contract import (
        _anchored_attempt,
    )

    gates = _gates()
    plan = gates._accept_semantic_investigation_plan(
        goal_class="analyze",
        comparison_requested=False,
        target_identities=[],
        evidence_needed=[
            {
                "description": "Contagem de processos ativos",
                "evidence_source": "process",
            }
        ],
        expected_delivery="aggregation",
        correlation="g2-unbound-complete",
    )
    hit = _anchored_attempt(
        root="PROC-0001",
        vocabulary=("process", "search"),
        structured={"success": True, "data": {"total": 109}},
    )
    terminal = GovernedCapabilityAttempt(
        status=GovernedCapabilityStatus.NOT_APPLICABLE,
        correlation_id="g2-unbound-complete",
        content=None,
        limitations=("insufficient_evidence",),
    )
    declared = InvestigationAnswer(
        schema_version="1",
        status=InvestigationAnswerStatus.COMPLETE,
        answer="Existem 200 processos ativos.",
        evidence_refs=(5,),  # unbound
    )
    out = _apply_declared_answer(
        terminal=terminal,
        declared_answer=declared,
        collected=(hit,),
        plan=plan,
        correlation="g2-unbound-complete",
        unbound_outcome=None,
    )
    assert "declared_status_overridden" in out.limitations
    assert out.status is not GovernedCapabilityStatus.SUCCESS


# ---------------- R5 pagination negatives -----------------------------


def test_r5_n1_duplicate_page_does_not_inflate_collection():
    agg = aggregate_paginated_pages(
        [
            _page(page=1, n=40, has_more=True, total_count=109, id_offset=0),
            _page(page=1, n=40, has_more=False, total_count=109, id_offset=0),
        ]
    )
    assert agg.failed is True
    assert agg.failure_reason == "duplicate_page"
    assert resolve_count_semantics(None, aggregation=agg).total is None


def test_r5_n2_duplicate_record_rejects_false_total():
    # Without owner total: duplicate ids keep the walk incomplete and
    # must not invent a recomputed total from merged lengths.
    p2 = _page(page=2, n=5, has_more=False, id_offset=10)
    p2["items"][0]["id"] = 1
    agg = aggregate_paginated_pages(
        [_page(page=1, n=10, has_more=True, id_offset=0), p2]
    )
    assert agg.complete is False
    assert agg.duplicate_ids
    assert agg.failure_reason == "duplicate_ticket_ids"
    assert resolve_count_semantics(None, aggregation=agg).total is None


def test_r5_n6_authoritative_total_conflict():
    agg = aggregate_paginated_pages(
        [
            _page(page=1, n=40, has_more=True, total_count=109, id_offset=0),
            _page(page=2, n=40, has_more=False, total_count=99, id_offset=40),
        ]
    )
    assert agg.failed is True
    assert agg.failure_reason == "authoritative_total_conflict"


def test_r5_n7_missing_page_incomplete():
    agg = aggregate_paginated_pages(
        [
            _page(page=1, n=40, has_more=True, total_count=109, id_offset=0),
            _page(page=3, n=29, has_more=False, total_count=109, id_offset=80),
        ]
    )
    assert agg.failed is True
    assert agg.failure_reason == "missing_intermediate_page"


def test_r5_n8_truncated_walk_without_total_not_complete():
    # Truncation without authoritative total must stay partial. When the
    # owner publishes total_count, count completeness is authoritative
    # (see aggregator contract); enumeration delivery is gated in R5-N10.
    agg = aggregate_paginated_pages(
        [
            _page(page=1, n=40, has_more=True, id_offset=0),
            _page(page=2, n=40, has_more=True, id_offset=40),
        ]
    )
    assert agg.complete is False
    assert resolve_count_semantics(None, aggregation=agg).kind is (
        CountResolutionKind.PARTIAL_UNKNOWN
    )


def test_r5_n9_budget_partial_honest():
    pages = [
        _page(page=i, n=40, has_more=True, id_offset=(i - 1) * 40)
        for i in range(1, 6)
    ]
    agg = aggregate_paginated_pages(pages, max_pages=2)
    assert agg.complete is False
    assert agg.failure_reason == "max_pages_exceeded"


def test_r5_positive_three_page_walk_109():
    """Sibling of live R5: 40+40+29 with stable total 109."""
    pages = [
        _page(page=1, n=40, has_more=True, total_count=109, id_offset=0),
        _page(page=2, n=40, has_more=True, total_count=109, id_offset=40),
        _page(page=3, n=29, has_more=False, total_count=109, id_offset=80),
    ]
    agg = aggregate_paginated_pages(pages)
    assert agg.complete is True
    assert agg.unique_count == 109
    assert resolve_count_semantics(None, aggregation=agg).total == 109


def test_r5_n10_enumeration_not_satisfied_by_aggregate_total_alone():
    """Authoritative total alone does not prove enumeration delivery."""
    gates = _gates()
    plan = gates._accept_semantic_investigation_plan(
        goal_class="read",
        comparison_requested=False,
        target_identities=[],
        evidence_needed=[
            {
                "description": "Listagem de todos os processos",
                "evidence_source": "process",
                "operation": "read",
            }
        ],
        expected_delivery="enumeration",
        correlation="r5-n10",
    )
    assert plan is not None
    # Truncated page with authoritative total — not a complete walk.
    partial = _success_attempt(
        content="page slice",
        root="PROC-0001",
        structured={
            "success": True,
            "data": {
                "total": 109,
                "items": [{"id": f"p-{i}"} for i in range(40)],
                "truncated": True,
                "pagination": {"page": 1, "page_size": 40, "has_more": True},
            },
        },
    )
    # Ensure process vocabulary for anchoring when helpers support it.
    partial = dataclasses.replace(
        partial,
        limitations=tuple(partial.limitations) + ("result_truncated",),
    )
    coverage = _evaluate_material_obligations(
        obligations=plan.evidence_needed,
        business=(partial,),
        delivery=_plan_delivery_mode(plan),
    )
    assert all(state != OBLIGATION_SATISFIED for _, state in coverage)


# ---------------- invented_record_tokens generalization ---------------


def test_invented_leading_zeros_accepted_when_user_named():
    invented = invented_record_tokens(
        ["00012345"],
        input_text="estrutura do produto 00012345",
        prior_turns=(),
    )
    assert invented == []


def test_invented_alphanumeric_with_separator_rejected_when_absent():
    invented = invented_record_tokens(
        ["PROC-9999"],
        input_text="liste processos ativos",
        prior_turns=(),
    )
    assert invented == ["PROC-9999"]


def test_invented_code_only_in_prior_user_turn_accepted():
    class _Turn:
        def __init__(self, content: str) -> None:
            self.content = content

    invented = invented_record_tokens(
        ["90260921"],
        input_text="pode continuar",
        prior_turns=(
            _Turn("Quero a estrutura do produto 90260921"),
            _Turn("Qual é o código do produto?"),
        ),
    )
    assert invented == []


def test_invented_common_word_not_codey():
    invented = invented_record_tokens(
        ["produto", "estrutura", "ativos"],
        input_text="Quero ver a estrutura de um produto ativos",
        prior_turns=(),
    )
    assert invented == []


def test_invented_model_fabricated_numeric_code_absent():
    invented = invented_record_tokens(
        ["P12345", "99988877"],
        input_text="Quero ver a estrutura de um produto.",
        prior_turns=(),
    )
    assert "P12345" in invented
    # Pure numeric literals are identifier-shaped; absent => invented.
    assert "99988877" in invented


def test_invented_user_correction_in_second_turn_accepted():
    class _Turn:
        def __init__(self, content: str) -> None:
            self.content = content

    invented = invented_record_tokens(
        ["90260921"],
        input_text="desculpe, o código correto é 90260921",
        prior_turns=(
            _Turn("Quero ver a estrutura de um produto."),
            _Turn("Qual é o código do produto?"),
            _Turn("P12345"),
        ),
    )
    assert invented == []
