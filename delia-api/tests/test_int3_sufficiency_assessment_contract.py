"""INT-3 sufficiency specialist contract (DELIA_THREE_AGENT_EXPERIMENT).

Three-Agent experimental variant — boundary proofs for the
Suficiência stage layered on the Compreensão→Investigação split:

- the Application acceptor (``_accept_sufficiency_assessment``) is the
  only validator — a proposal may downgrade, never promote;
- ``PROPOSE_COMPLETION`` without deterministic proof is rejected;
- ``CONTINUE_INVESTIGATION`` requires a demonstrable gap, an eligible
  capability inside the accepted plan and remaining shared budget —
  and yields at most ONE bounded INT-1 re-entry per turn;
- the sufficiency specialist's surface carries ZERO tools;
- the turn budget is shared, never reset;
- flag OFF keeps exact baseline parity.
"""

from __future__ import annotations

from app.application.capability_provision.contracts import (
    SemanticMismatch,
    SemanticMismatchKind,
    SufficiencyAssessmentProposal,
    SufficiencyContinuation,
    SufficiencyVerdict,
)
from app.application.capability_provision.governed_capability_orchestrator import (
    OperationalCapabilityOrchestrator,
)
from app.application.capability_provision.semantic_capability_support import (
    MaterialObligation,
    OBLIGATION_INCONCLUSIVE,
    OBLIGATION_SATISFIED,
    OBLIGATION_UNSATISFIED,
    _accept_sufficiency_assessment,
)
from app.application.interaction.capability_attempt import (
    GovernedCapabilityStatus,
)
from app.application.interaction.turn_budget import TurnDeadline
from app.application.model_invocation.invoke_model import (
    InvokeModel,
)
from app.infrastructure.orchestration.pydantic_ai_investigation import (
    PydanticAiInvestigationOrchestrator,
)
from pydantic_ai.messages import (
    ModelResponse,
    ToolCallPart,
)
from pydantic_ai.models.function import FunctionModel
from tests.support.capability_fixtures import (
    FakeProposalModel,
    _providers,
    load_test_orchestration_instructions,
)
from tests.support.native_mcp_fixtures import (
    alpha_beta_servers,
    native_toolset_stub,
)


def _obligations() -> tuple[MaterialObligation, ...]:
    return (
        MaterialObligation(
            description="listagem de processos",
            evidence_source="process",
            operation="read",
        ),
        MaterialObligation(
            description="estrutura do produto",
            evidence_source="get_product_structure",
            operation="read",
        ),
    )


def _proposal(
    verdict: SufficiencyVerdict,
    **kwargs,
) -> SufficiencyAssessmentProposal:
    return SufficiencyAssessmentProposal(
        verdict_proposal=verdict, **kwargs
    )


# -------------------------------------------------------------------
# Application acceptor — field-level validation
# -------------------------------------------------------------------


def test_propose_completion_without_deterministic_proof_rejected():
    """INT3-01: completion may only be proposed when every obligation
    is SATISFIED in the deterministic coverage."""
    acceptance = _accept_sufficiency_assessment(
        proposal=_proposal(SufficiencyVerdict.PROPOSE_COMPLETION),
        obligations=_obligations(),
        coverage=(
            ("listagem de processos", OBLIGATION_SATISFIED),
            ("estrutura do produto", OBLIGATION_UNSATISFIED),
        ),
        eligible_capability_ids=("alpha.search_items",),
        budget_remaining=True,
        continuation_used=False,
    )
    assert not acceptance.accepted
    assert "completion_unproven" in str(
        acceptance.rejection["errors"]["verdict_proposal"]
    )


def test_propose_completion_with_full_proof_accepted():
    acceptance = _accept_sufficiency_assessment(
        proposal=_proposal(SufficiencyVerdict.PROPOSE_COMPLETION),
        obligations=_obligations(),
        coverage=(
            ("listagem de processos", OBLIGATION_SATISFIED),
            ("estrutura do produto", OBLIGATION_SATISFIED),
        ),
        eligible_capability_ids=("alpha.search_items",),
        budget_remaining=True,
        continuation_used=False,
    )
    assert acceptance.accepted


def test_continue_without_unmet_obligation_rejected():
    """INT3-02: continuation requires a demonstrable gap — all
    obligations already SATISFIED means nothing to continue for."""
    acceptance = _accept_sufficiency_assessment(
        proposal=_proposal(
            SufficiencyVerdict.CONTINUE_INVESTIGATION,
            unmet_obligations=("listagem de processos",),
            recommended_continuation=SufficiencyContinuation(
                capability="alpha.search_items",
                arguments={"query": "processos"},
            ),
        ),
        obligations=_obligations(),
        coverage=(
            ("listagem de processos", OBLIGATION_SATISFIED),
            ("estrutura do produto", OBLIGATION_SATISFIED),
        ),
        eligible_capability_ids=("alpha.search_items",),
        budget_remaining=True,
        continuation_used=False,
    )
    assert not acceptance.accepted
    assert (
        acceptance.rejection["errors"]["verdict_proposal"]
        == "continuation_without_unmet_obligation"
    )


def test_continue_foreign_capability_and_unnamed_gap_rejected():
    """INT3-03: a continuation naming a capability outside the
    eligible surface and unmet obligations outside the accepted plan
    is rejected on both fields."""
    acceptance = _accept_sufficiency_assessment(
        proposal=_proposal(
            SufficiencyVerdict.CONTINUE_INVESTIGATION,
            unmet_obligations=("obrigação inventada",),
            recommended_continuation=SufficiencyContinuation(
                capability="foreign.exfiltrate",
                arguments={"query": "x"},
            ),
        ),
        obligations=_obligations(),
        coverage=(
            ("listagem de processos", OBLIGATION_UNSATISFIED),
            ("estrutura do produto", OBLIGATION_SATISFIED),
        ),
        eligible_capability_ids=("alpha.search_items",),
        budget_remaining=True,
        continuation_used=False,
    )
    assert not acceptance.accepted
    assert "references_outside_accepted_plan" in str(
        acceptance.rejection["errors"]["unmet_obligations"]
    )
    assert "capability_not_eligible" in str(
        acceptance.rejection["errors"]["recommended_continuation"]
    )
    assert acceptance.rejection["errors"]["unmet_obligations"] != (
        "no_demonstrable_gap_named"
    )


def test_continue_budget_and_quota_gates():
    """INT3-04a: a valid continuation still fails closed when the
    shared budget is exhausted or the re-entry quota consumed."""
    proposal = _proposal(
        SufficiencyVerdict.CONTINUE_INVESTIGATION,
        unmet_obligations=("listagem de processos",),
        recommended_continuation=SufficiencyContinuation(
            capability="alpha.search_items",
            arguments={"query": "processos"},
        ),
    )
    coverage = (
        ("listagem de processos", OBLIGATION_INCONCLUSIVE),
        ("estrutura do produto", OBLIGATION_SATISFIED),
    )
    for kwargs, expected in (
        (
            {"budget_remaining": False},
            "continuation_budget_exhausted",
        ),
        (
            {"continuation_used": True},
            "continuation_limit_reached",
        ),
    ):
        acceptance = _accept_sufficiency_assessment(
            proposal=proposal,
            obligations=_obligations(),
            coverage=coverage,
            eligible_capability_ids=("alpha.search_items",),
            **{
                "budget_remaining": True,
                "continuation_used": False,
                **kwargs,
            },
        )
        assert not acceptance.accepted
        assert acceptance.rejection["errors"]["budget"] == expected

    acceptance = _accept_sufficiency_assessment(
        proposal=proposal,
        obligations=_obligations(),
        coverage=coverage,
        eligible_capability_ids=("alpha.search_items",),
        budget_remaining=True,
        continuation_used=False,
    )
    assert acceptance.accepted
    assert acceptance.continuation is not None
    assert acceptance.continuation.capability == "alpha.search_items"
    assert acceptance.unmet_obligations == (
        "listagem de processos",
    )


def test_typed_semantic_mismatch_accepted_as_limitations():
    """INT3-05: a typed mismatch inside the vocabulary is accepted
    and propagated as typed limitations — never fabricated facts."""
    acceptance = _accept_sufficiency_assessment(
        proposal=_proposal(
            SufficiencyVerdict.REPORT_PARTIAL,
            unmet_obligations=("estrutura do produto",),
            semantic_mismatches=(
                SemanticMismatch(
                    kind=SemanticMismatchKind.WRONG_FILTER,
                    detail="owner returned unfiltered window",
                ),
            ),
            limitations=("page window truncated",),
        ),
        obligations=_obligations(),
        coverage=(
            ("listagem de processos", OBLIGATION_INCONCLUSIVE),
            ("estrutura do produto", OBLIGATION_UNSATISFIED),
        ),
        eligible_capability_ids=("alpha.search_items",),
        budget_remaining=True,
        continuation_used=False,
    )
    assert acceptance.accepted
    assert "int3_mismatch:wrong_filter" in acceptance.limitations
    assert "int3_verdict:report_partial" in acceptance.limitations


def test_unknown_mismatch_kind_rejected():
    acceptance = _accept_sufficiency_assessment(
        proposal=_proposal(
            SufficiencyVerdict.REPORT_PARTIAL,
            semantic_mismatches=(
                SemanticMismatch(kind="owner_said_so"),  # type: ignore[arg-type]
            ),
        ),
        obligations=_obligations(),
        coverage=(
            ("listagem de processos", OBLIGATION_SATISFIED),
            ("estrutura do produto", OBLIGATION_SATISFIED),
        ),
        eligible_capability_ids=("alpha.search_items",),
        budget_remaining=True,
        continuation_used=False,
    )
    assert not acceptance.accepted
    assert (
        acceptance.rejection["errors"]["semantic_mismatches"]
        == "unknown_mismatch_kind"
    )


def test_request_clarification_needs_question():
    acceptance = _accept_sufficiency_assessment(
        proposal=_proposal(
            SufficiencyVerdict.REQUEST_CLARIFICATION,
        ),
        obligations=_obligations(),
        coverage=(
            ("listagem de processos", OBLIGATION_UNSATISFIED),
            ("estrutura do produto", OBLIGATION_UNSATISFIED),
        ),
        eligible_capability_ids=("alpha.search_items",),
        budget_remaining=True,
        continuation_used=False,
    )
    assert not acceptance.accepted
    assert (
        acceptance.rejection["errors"]["clarification_question"]
        == "missing_clarification_question"
    )


# -------------------------------------------------------------------
# Three-Agent composition — boundary + budget + parity
# -------------------------------------------------------------------


def _gates(providers=None) -> OperationalCapabilityOrchestrator:
    return OperationalCapabilityOrchestrator(
        providers or _providers(),
        orchestration_instructions=load_test_orchestration_instructions(),
        invoke_model=InvokeModel(FakeProposalModel(())),
    )


def _tool_names(info) -> set[str]:
    return {str(t.name) for t in info.function_tools}


def _is_comprehension(info) -> bool:
    names = _tool_names(info)
    return "declare_investigation_goal" in names and not any(
        "." in n for n in names
    )


def _is_sufficiency(info) -> bool:
    return not _tool_names(info)


def _valid_goal_call() -> ToolCallPart:
    return ToolCallPart(
        "declare_investigation_goal",
        {
            "goal_class": "read",
            "expected_delivery": "enumeration",
            "business_subject": "processos",
            "evidence_needed": [
                {
                    "description": "listagem de processos",
                    "evidence_source": "process",
                    "operation": "read",
                }
            ],
        },
    )


def _comp_outcome() -> ModelResponse:
    return ModelResponse(
        parts=[
            ToolCallPart(
                "final_result",
                {"status": "proposal_submitted", "note": ""},
            )
        ]
    )


def _answer(status: str = "partial") -> ModelResponse:
    return ModelResponse(
        parts=[
            ToolCallPart(
                "final_result",
                {
                    "schema_version": "1",
                    "status": status,
                    "answer": "done",
                    "evidence_refs": [],
                    "unmet_obligations": [],
                    "limitations": [],
                },
            )
        ]
    )


def _sufficiency_response(payload: dict) -> ModelResponse:
    return ModelResponse(
        parts=[ToolCallPart("final_result", payload)]
    )


def _suff_continue() -> ModelResponse:
    return _sufficiency_response(
        {
            "schema_version": "1",
            "verdict_proposal": "continue_investigation",
            "unmet_obligations": ["listagem de processos"],
            "gap_analysis": "first page only",
            "recommended_continuation": {
                "capability": "alpha.search_items",
                "arguments": {"arguments": {"query": "processos"}},
                "rationale": "page 2",
            },
        }
    )


def _suff_insufficient() -> ModelResponse:
    return _sufficiency_response(
        {
            "schema_version": "1",
            "verdict_proposal": "report_insufficient",
            "gap_analysis": "owner evidence absent",
        }
    )


def _engine(fn, **kwargs) -> PydanticAiInvestigationOrchestrator:
    return PydanticAiInvestigationOrchestrator(
        _gates(),
        model=FunctionModel(fn),
        request_limit=12,
        tool_calls_limit=8,
        agent_retries=1,
        two_agent_experiment=True,
        three_agent_experiment=True,
        **kwargs,
    )


def test_sufficiency_stage_has_zero_owner_tools():
    """INT3-06: the sufficiency Agent surface carries NO tools —
    no owner path, no declare, no clarify tool."""
    gates = _gates()
    surfaces: dict = {}

    def _fn(messages, info):
        names = _tool_names(info)
        if _is_sufficiency(info):
            surfaces["sufficiency"] = names
            return _suff_insufficient()
        if _is_comprehension(info):
            prior = sum(
                1 for m in messages if isinstance(m, ModelResponse)
            )
            if prior == 0:
                return ModelResponse(parts=[_valid_goal_call()])
            return _comp_outcome()
        prior = sum(
            1 for m in messages if isinstance(m, ModelResponse)
        )
        if prior == 0:
            return ModelResponse(
                parts=[
                    ToolCallPart(
                        "alpha.search_items",
                        {"arguments": {"query": "processos"}},
                    )
                ]
            )
        return _answer()

    engine = _engine(_fn)
    with native_toolset_stub(alpha_beta_servers()):
        attempt = engine.attempt(
            "liste os processos ativos",
            correlation_id="int3-tools",
        )
    assert surfaces["sufficiency"] == set()
    assert attempt.status in (
        GovernedCapabilityStatus.SUCCESS,
        GovernedCapabilityStatus.NOT_APPLICABLE,
        GovernedCapabilityStatus.CLARIFICATION_REQUIRED,
        GovernedCapabilityStatus.SOURCE_UNAVAILABLE,
    )


def test_valid_continue_triggers_exactly_one_bounded_reentry():
    """INT3-04b: an accepted CONTINUE_INVESTIGATION triggers ONE
    bounded INT-1 re-entry; the quota is then consumed."""
    import pydantic_ai.agent as _agent_mod

    runs: list = []
    original = _agent_mod.Agent.run_sync

    def _spy(self, *args, **kwargs):
        runs.append(kwargs.get("usage_limits"))
        return original(self, *args, **kwargs)

    def _fn(messages, info):
        if _is_sufficiency(info):
            return _suff_continue()
        if _is_comprehension(info):
            prior = sum(
                1 for m in messages if isinstance(m, ModelResponse)
            )
            if prior == 0:
                return ModelResponse(parts=[_valid_goal_call()])
            return _comp_outcome()
        prior = sum(
            1 for m in messages if isinstance(m, ModelResponse)
        )
        if prior == 0:
            return ModelResponse(
                parts=[
                    ToolCallPart(
                        "alpha.search_items",
                        {"arguments": {"query": "processos"}},
                    )
                ]
            )
        return _answer("partial")

    _agent_mod.Agent.run_sync = _spy
    try:
        engine = _engine(_fn)
        with native_toolset_stub(alpha_beta_servers()):
            attempt = engine.attempt(
                "liste os processos ativos",
                correlation_id="int3-reentry",
            )
    finally:
        _agent_mod.Agent.run_sync = original
    # comp + inv + suff + one re-entry = 4 native runs
    assert len(runs) == 4
    assert "sufficiency" not in str(attempt.error_code or "")


def test_shared_budget_no_reset_and_flag_off_parity():
    """INT3-07/08: sufficiency consumes the same turn budget
    (subtractive requests, zero tool calls); flag OFF preserves the
    exact two-Agent path with zero sufficiency runs."""
    import pydantic_ai.agent as _agent_mod

    usage_seen: list = []
    original = _agent_mod.Agent.run_sync

    def _spy(self, *args, **kwargs):
        usage_seen.append(kwargs.get("usage_limits"))
        return original(self, *args, **kwargs)

    def _fn(messages, info):
        if _is_sufficiency(info):
            return _suff_insufficient()
        if _is_comprehension(info):
            prior = sum(
                1 for m in messages if isinstance(m, ModelResponse)
            )
            if prior == 0:
                return ModelResponse(parts=[_valid_goal_call()])
            return _comp_outcome()
        prior = sum(
            1 for m in messages if isinstance(m, ModelResponse)
        )
        if prior == 0:
            return ModelResponse(
                parts=[
                    ToolCallPart(
                        "alpha.search_items",
                        {"arguments": {"query": "processos"}},
                    )
                ]
            )
        return _answer()

    _agent_mod.Agent.run_sync = _spy
    try:
        engine = _engine(_fn)
        with native_toolset_stub(alpha_beta_servers()):
            engine.attempt(
                "liste os processos ativos",
                correlation_id="int3-budget",
            )
        # 3 runs: comprehension, investigation, sufficiency
        assert len(usage_seen) == 3
        suff_limits = usage_seen[2]
        assert suff_limits is not None
        assert suff_limits.tool_calls_limit == 0
        # cumulative cap over the SHARED turn counter: allowance is a
        # subtractive share (≤ baseline//4), never a reset grant — the
        # cap is consumed-before + allowance and ≤ the full budget.
        consumed_before_suff = 5  # comp(2) + inv(3) in this fixture
        rl = suff_limits.request_limit or 0
        assert consumed_before_suff < rl <= (
            consumed_before_suff + 12 // 4
        )
        assert rl <= 12
        # flag OFF ⇒ only comp+inv runs
        usage_seen.clear()
        engine_off = PydanticAiInvestigationOrchestrator(
            _gates(),
            model=FunctionModel(_fn),
            request_limit=12,
            tool_calls_limit=8,
            agent_retries=1,
            two_agent_experiment=True,
            three_agent_experiment=False,
        )
        with native_toolset_stub(alpha_beta_servers()):
            engine_off.attempt(
                "liste os processos ativos",
                correlation_id="int3-off",
            )
        assert len(usage_seen) == 2
    finally:
        _agent_mod.Agent.run_sync = original
