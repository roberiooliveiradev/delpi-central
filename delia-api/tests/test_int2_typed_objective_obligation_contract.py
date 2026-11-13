"""INT-2 — typed objective, expected delivery and evidence obligations.

Bounded EXTEND of the existing INT-1 plan contract: the Agent must be
able to declare a typed objective whose expected delivery
(enumeration / aggregation / explanation / record_detail / comparison)
and material obligations reach the finalize coverage evaluator as a
``SemanticInvestigationPlan``. Without a declaration the coverage
verdict stays ``coverage_unknown`` — the INT-2 gap (doc 324).

Deterministic contract tests only; real inference behaviour requires
the isolated real-model evaluation.
"""

from __future__ import annotations

from app.application.model_invocation.invoke_model import InvokeModel
from app.application.capability_provision.governed_capability_orchestrator import (
    OperationalCapabilityOrchestrator,
)
from app.infrastructure.orchestration import pydantic_ai_investigation as pai
from tests.support.capability_fixtures import (
    FakeProposalModel,
    _providers,
    load_test_orchestration_instructions,
)


def _gates() -> OperationalCapabilityOrchestrator:
    return OperationalCapabilityOrchestrator(
        _providers(),
        orchestration_instructions=load_test_orchestration_instructions(),
        invoke_model=InvokeModel(FakeProposalModel(())),
    )


# -------------------------------------------------------------------
# RQ-INT2-01 — typed expected delivery on the existing goal contract
# -------------------------------------------------------------------


def test_expected_delivery_enumeration_reaches_typed_goal():
    plan = _gates()._accept_semantic_investigation_plan(
        goal_class="read",
        comparison_requested=False,
        target_identities=[],
        evidence_needed=["process registry coverage"],
        business_subject="registered transformation processes",
        expected_delivery="enumeration",
        correlation="int2-enum",
    )
    assert plan is not None
    assert plan.goal.declared is True
    assert plan.goal.output_mode == "enumeration"
    assert plan.evidence_needed == ("process registry coverage",)


def test_expected_delivery_aggregation_and_explanation_accepted():
    gates = _gates()
    for delivery in ("aggregation", "explanation"):
        plan = gates._accept_semantic_investigation_plan(
            goal_class="analyze",
            comparison_requested=False,
            target_identities=[],
            evidence_needed=["metric scope"],
            expected_delivery=delivery,
            correlation=f"int2-{delivery}",
        )
        assert plan is not None
        assert plan.goal.output_mode == delivery


def test_invalid_expected_delivery_rejects_plan():
    plan = _gates()._accept_semantic_investigation_plan(
        goal_class="read",
        comparison_requested=False,
        target_identities=["90260921"],
        evidence_needed=[],
        expected_delivery="give me the answer",
        correlation="int2-invalid-delivery",
    )
    assert plan is None


def test_omitted_expected_delivery_defaults_unspecified():
    """Contract stays backward-compatible: omitted delivery remains
    ``unspecified`` — the honest 'unproven delivery type' state, never
    a fabricated classification."""
    plan = _gates()._accept_semantic_investigation_plan(
        goal_class="read",
        comparison_requested=False,
        target_identities=["90260921"],
        evidence_needed=["90260921"],
        correlation="int2-default-delivery",
    )
    assert plan is not None
    assert plan.goal.output_mode == "unspecified"


def test_declaration_is_not_authorization():
    """AC-06/security: a declared plan never grants capability access
    — it only carries typed interpretation fields."""
    plan = _gates()._accept_semantic_investigation_plan(
        goal_class="create_or_modify",
        comparison_requested=False,
        target_identities=[],
        evidence_needed=[],
        expected_delivery="unspecified",
        correlation="int2-authz",
    )
    assert plan is not None
    # goal class exists in the canonical vocabulary, but the plan holds
    # no permission surface — only semantic fields.
    assert plan.goal.execution_bound == "unrestricted"
    assert not hasattr(plan, "permissions")


# -------------------------------------------------------------------
# RQ-INT2-05 — coverage verdict becomes provable with a valid plan
# -------------------------------------------------------------------


def test_plan_obligations_reach_coverage_evaluator():
    """With evidence_needed populated, ``_evaluate_material_obligations``
    must produce typed states (never silently coverage_unknown)."""
    from app.application.capability_provision.semantic_capability_support import (
        _evaluate_material_obligations,
        OBLIGATION_SATISFIED,
        OBLIGATION_UNSATISFIED,
    )

    satisfied = _evaluate_material_obligations(
        obligations=("90260921",), business=()
    )
    # No business evidence at all → the obligation is honestly
    # UNSATISFIED (not unknown) because a typed plan existed.
    assert satisfied == (("90260921", OBLIGATION_UNSATISFIED),)
    assert OBLIGATION_SATISFIED != OBLIGATION_UNSATISFIED


# -------------------------------------------------------------------
# RQ-INT2-03 — typed evidence kinds (doc 301): subject scope vs identity
# -------------------------------------------------------------------

from app.application.capability_provision.semantic_capability_support import (  # noqa: E402
    OBLIGATION_SATISFIED,
    OBLIGATION_UNSATISFIED,
    _evaluate_material_obligations,
)
from app.application.interaction.capability_attempt import (  # noqa: E402
    GovernedCapabilityAttempt,
    GovernedCapabilityProvenance,
    GovernedCapabilityStatus,
)
from app.domain.evidence.model import SourceRef  # noqa: E402
from app.domain.specialist_interop.model import (  # noqa: E402
    InteropProtocol,
    SpecialistOutcome,
    SpecialistResultProvenance,
    SpecialistResultStatus,
)


def _bound_attempt(*, root: str = "PROC-0001", child: str | None = None):
    """Complete, fully-provenant business evidence attempt."""
    item: dict = {"code": root, "label": f"label-{root}"}
    if child:
        item["components"] = [{"code": child, "label": f"child-{child}"}]
    outcome = SpecialistOutcome(
        status=SpecialistResultStatus.COMPLETED,
        content_text=f"records for {root}",
        structured={"items": [item]},
        provenance=SpecialistResultProvenance(
            specialist_id="owner",
            remote_name="read",
            protocol=InteropProtocol.MCP,
            correlation_id="int2-oblig",
            observed_at="2026-01-01T00:00:00Z",
        ),
        is_complete=True,
    )
    return GovernedCapabilityAttempt(
        status=GovernedCapabilityStatus.SUCCESS,
        correlation_id="int2-oblig",
        content=f"records for {root}",
        limitations=(),
        provenance=GovernedCapabilityProvenance(
            source_refs=(
                SourceRef(
                    source_id=root,
                    source_system="owner",
                    provider_name="owner",
                    observed_at="2026-01-01T00:00:00Z",
                ),
            ),
            specialist_id="owner",
            remote_capability="read",
            action_id="read",
            protocol=InteropProtocol.MCP.value,
            observed_at="2026-01-01T00:00:00Z",
            correlation_id="int2-oblig",
            is_complete=True,
        ),
        outcome=outcome,
    )


def test_subject_obligation_satisfied_by_bound_business_evidence():
    """Non-identifier obligation (collection/metric/explanatory scope)
    is satisfied by authoritative bound business evidence — the
    deterministic layer proves governed evidence exists; semantic
    pertinence stays model-declared (evidence-by-kind)."""
    coverage = _evaluate_material_obligations(
        obligations=("process registry coverage",),
        business=(_bound_attempt(root="PROC-0001"),),
    )
    assert coverage == (("process registry coverage", OBLIGATION_SATISFIED),)


def test_subject_obligation_unsatisfied_without_evidence():
    coverage = _evaluate_material_obligations(
        obligations=("supplier count",), business=()
    )
    assert coverage == (("supplier count", OBLIGATION_UNSATISFIED),)


def test_identity_obligation_keeps_strict_matching():
    """Identifier obligations never relax into subject matching: a
    bound attempt under a *different* root must not satisfy REF05."""
    coverage = _evaluate_material_obligations(
        obligations=("90260921",),
        business=(_bound_attempt(root="OTHER-123"),),
    )
    assert coverage == (("90260921", OBLIGATION_UNSATISFIED),)
    satisfied = _evaluate_material_obligations(
        obligations=("90260921",),
        business=(_bound_attempt(root="90260921"),),
    )
    assert satisfied == (("90260921", OBLIGATION_SATISFIED),)


def test_descriptor_with_identifier_literal_stays_strict():
    """A descriptive obligation containing an identifier literal
    ('estrutura do produto 90260921') still requires that identity in
    bound evidence — prose alone never closes coverage."""
    coverage = _evaluate_material_obligations(
        obligations=("estrutura do produto 90260921",),
        business=(_bound_attempt(root="PROC-0001"),),
    )
    assert coverage == (
        ("estrutura do produto 90260921", OBLIGATION_UNSATISFIED),
    )
    satisfied = _evaluate_material_obligations(
        obligations=("estrutura do produto 90260921",),
        business=(_bound_attempt(root="90260921"),),
    )
    assert satisfied == (
        ("estrutura do produto 90260921", OBLIGATION_SATISFIED),
    )


def test_obligations_bind_distinct_attempts():
    """Two obligations cannot collapse onto one attempt: distinct
    binding keeps multi-obligation coverage honest."""
    coverage = _evaluate_material_obligations(
        obligations=("registry coverage", "dashboard formats"),
        business=(_bound_attempt(root="PROC-0001"),),
    )
    states = dict(coverage)
    assert states["registry coverage"] == OBLIGATION_SATISFIED
    assert states["dashboard formats"] == OBLIGATION_UNSATISFIED


# -------------------------------------------------------------------
# Instruction contract — v2-4 typed-objective lineage
# -------------------------------------------------------------------


def _v24_text() -> str:
    return pai.load_selected_investigation_instructions(
        instruction_version="generalist-semantic-v2-4-typed-objective"
    ).text


def test_v2_4_declares_typed_goal_declaration_rule():
    """AC-01/AC-02: the instruction must require a typed declaration
    for business-evidence objectives — the OPTIONAL/single-READ skip
    clause was the proven root cause of plan=None."""
    text = _v24_text()
    assert "declare_investigation_goal" in text
    lowered = text.casefold()
    assert "expected_delivery" in lowered or "expected delivery" in lowered
    assert "evidence_needed" in lowered or "evidence needed" in lowered
    # The proven-broken 'skip a simple single READ' clause must be gone.
    assert "skip it for a simple single read" not in lowered


def test_v2_4_delivery_vocabulary_covers_int2_minimum():
    text = _v24_text().casefold()
    for delivery in ("enumeration", "aggregation", "explanation"):
        assert delivery in text


def test_v2_4_obligations_derive_from_objective_not_keywords():
    text = _v24_text().casefold()
    assert "material" in text
    assert "objective" in text
    # Explicit anti-hardcode guard: obligations come from the declared
    # objective, not from phrase matching.
    for banned in (
        "90260921",
        "process.search",
        "get_product_structure",
        " for davi",
        " for teo",
    ):
        assert banned not in text


def test_v2_4_declaration_is_semantic_not_authorization():
    text = _v24_text()
    lowered = text.casefold()
    assert "semantic proposal" in lowered or "not authorization" in lowered


def test_v2_4_extends_v2_3_preserving_governed_clauses():
    """Bounded EXTEND: every v2-3 rule block survives verbatim except
    the replaced declare-goal clause (the proven root cause)."""
    v23 = pai.load_selected_investigation_instructions(
        instruction_version="generalist-semantic-v2-3-enumeration-intent"
    ).text
    v24 = _v24_text()
    preamble, *blocks = v23.split("\n- ")
    assert v24.startswith(preamble)
    cursor = 0
    replaced = 0
    for block in blocks:
        needle = "- " + block
        if "declare_investigation_goal` is OPTIONAL" in needle:
            # Root-cause clause replaced by the typed channel contract.
            replaced += 1
            continue
        if needle.startswith(
            "- Understand the user's objective before calling tools."
        ):
            # Comprehension-step bullet extended to require the typed
            # declaration up front (second documented replacement).
            replaced += 1
            continue
        idx = v24.find(needle, cursor)
        assert idx != -1, f"v2-3 block dropped from v2-4: {block[:60]!r}"
        cursor = idx + len(needle)
    assert replaced == 2
    assert len(v24) > len(v23)


def test_v2_4_is_registered_and_selectable():
    selected = pai.load_selected_investigation_instructions(
        instruction_version="generalist-semantic-v2-4-typed-objective"
    )
    assert selected.instruction_version == (
        "generalist-semantic-v2-4-typed-objective"
    )
    assert selected.text_fingerprint
    default = pai.load_selected_investigation_instructions()
    assert (
        default.instruction_version
        == "generalist-semantic-v2-4-typed-objective"
    )


# -------------------------------------------------------------------
# RQ-INT2-02 — invalid declaration gets bounded-vocabulary feedback
# (real-model replay: eval or-qwen14b-52571a726980)
# -------------------------------------------------------------------


def test_invalid_goal_class_gets_vocabulary_feedback_and_recovers():
    """The real model invented ``goal_class="enumeration"`` — outside
    the bounded vocabulary — and retried blind until the tool budget
    ran out. A rejection must echo the valid vocabularies so the next
    declaration can self-correct into an accepted plan."""
    import json

    from pydantic_ai.messages import (
        ModelRequest,
        ModelResponse,
        ToolCallPart,
        ToolReturnPart,
    )
    from pydantic_ai.models.function import FunctionModel

    from app.application.interaction.turn_budget import TurnDeadline
    from app.infrastructure.orchestration.pydantic_ai_investigation import (
        PydanticAiInvestigationOrchestrator,
    )
    from tests.support.native_mcp_fixtures import (
        alpha_beta_servers,
        native_toolset_stub,
    )
    from tests.test_pydantic_ai_real_owner_tool_loop_rework import (
        _final_answer,
    )
    from tests.test_pydantic_ai_semantic_rework import (
        _gates as _loop_gates,
        _success_attempt,
    )

    gates = _loop_gates()
    catalog = gates._project_semantic_tool_catalog(
        correlation="c", deadline=TurnDeadline.start(30.0)
    )
    tool_name = catalog[0]["capability_id"]

    def _spy(**kwargs):
        return _success_attempt(content="registro PROC-0001", root="PROC-0001")

    gates._governed_semantic_tool_invoke = _spy  # type: ignore[method-assign]

    seen_returns: list[str] = []
    declared: dict = {}

    original_accept = gates._accept_semantic_investigation_plan

    def _accept_spy(**kwargs):
        plan = original_accept(**kwargs)
        declared.setdefault("attempts", []).append(
            {"goal_class": kwargs.get("goal_class"), "accepted": plan is not None}
        )
        return plan

    gates._accept_semantic_investigation_plan = _accept_spy  # type: ignore[method-assign]

    def _fn(messages, _info):
        tool_returns = [
            m for m in messages
            if isinstance(m, ModelRequest)
            and any(isinstance(p, ToolReturnPart) for p in m.parts)
        ]
        for req in tool_returns:
            for part in req.parts:
                if (
                    isinstance(part, ToolReturnPart)
                    and part.tool_name == "declare_investigation_goal"
                    and str(part.content) not in seen_returns
                ):
                    seen_returns.append(str(part.content))
        n_returns = sum(
            1
            for req in tool_returns
            for part in req.parts
            if isinstance(part, ToolReturnPart)
        )
        if n_returns == 0:
            # First divergence observed in the real trace: model guesses
            # a delivery-shaped goal_class outside the bounded set.
            return ModelResponse(
                parts=[
                    ToolCallPart(
                        "declare_investigation_goal",
                        {
                            "goal_class": "enumeration",
                            "expected_delivery": "enumeration",
                            "evidence_needed": ["registry coverage"],
                        },
                    )
                ]
            )
        if n_returns == 1:
            # Corrected declaration using the echoed vocabulary.
            return ModelResponse(
                parts=[
                    ToolCallPart(
                        "declare_investigation_goal",
                        {
                            "goal_class": "read",
                            "expected_delivery": "enumeration",
                            "evidence_needed": ["registry coverage"],
                        },
                    )
                ]
            )
        if n_returns == 2:
            return ModelResponse(
                parts=[ToolCallPart(tool_name, {"arguments": {}})]
            )
        return _final_answer("registro PROC-0001", status="complete", refs=[0])

    engine = PydanticAiInvestigationOrchestrator(
        gates, model=FunctionModel(_fn), tool_calls_limit=6
    )
    with native_toolset_stub(alpha_beta_servers()):
        attempt = engine.attempt("quais processos cadastrados")

    assert seen_returns, "declare tool result must reach the model"
    rejected = json.loads(seen_returns[0])
    assert rejected["status"] == "INVALID_GOAL"
    assert set(rejected["valid_goal_classes"]) == {
        "read", "analyze", "compare", "create_or_modify", "clarify",
    }
    assert set(rejected["valid_expected_delivery"]) == {
        "enumeration", "aggregation", "explanation",
        "record_detail", "comparison", "unspecified",
    }
    # Recovery path: the corrected declaration is accepted and coverage
    # is evaluated instead of staying coverage_unknown.
    assert declared["attempts"] == [
        {"goal_class": "enumeration", "accepted": False},
        {"goal_class": "read", "accepted": True},
    ]
    assert "coverage_unknown" not in attempt.limitations


# -------------------------------------------------------------------
# RQ-INT2-05 — coverage verdict regressions from the real trace
# (eval or-qwen14b-1aae39319659)
# -------------------------------------------------------------------


def test_prefixed_identifier_literal_binds_numeric_core():
    """Real-model obligations embed the identity inside a descriptor
    token (``structure_of_product_90260921``). The prefixed literal
    shares the authoritative numeric code — strict matching must
    extract the core, never treat the whole token as the owner code."""
    satisfied = _evaluate_material_obligations(
        obligations=("structure_of_product_90260921",),
        business=(_bound_attempt(root="90260921"),),
    )
    assert satisfied == (
        ("structure_of_product_90260921", OBLIGATION_SATISFIED),
    )
    # Wrong identity still fails — the numeric core is the contract.
    unsatisfied = _evaluate_material_obligations(
        obligations=("structure_of_product_90260921",),
        business=(_bound_attempt(root="OTHER-99"),),
    )
    assert unsatisfied == (
        ("structure_of_product_90260921", OBLIGATION_UNSATISFIED),
    )


def test_partial_declared_with_satisfied_plan_drops_coverage_unknown():
    """PARTIAL is honest self-report for a truncated enumeration —
    with a typed plan whose obligations are satisfied, coverage is
    *known*: ``coverage_unknown`` must not appear."""
    from app.application.capability_provision.contracts import (
        InvestigationAnswer,
        InvestigationAnswerStatus,
    )
    from app.application.capability_provision.semantic_capability_support import (
        _apply_declared_answer,
    )

    terminal = _bound_attempt(root="PROC-0001")
    plan = _gates()._accept_semantic_investigation_plan(
        goal_class="read",
        comparison_requested=False,
        target_identities=[],
        evidence_needed=["process registry coverage"],
        expected_delivery="enumeration",
        correlation="int2-partial",
    )
    declared = InvestigationAnswer(
        schema_version="1",
        status=InvestigationAnswerStatus.PARTIAL,
        answer="lista parcial de processos",
        evidence_refs=(0,),
        limitations=("result_truncated",),
    )
    result = _apply_declared_answer(
        terminal=terminal,
        declared_answer=declared,
        collected=(terminal,),
        plan=plan,
        correlation="int2-partial",
        unbound_outcome=None,
    )
    assert "coverage_unknown" not in result.limitations
    assert "declared_status_overridden" not in result.limitations
    assert result.content == "lista parcial de processos"


def test_partial_declared_with_unmet_obligation_stays_overridden():
    """PARTIAL prose may still be presented, but a material obligation
    without evidence keeps the claim honestly overridden."""
    from app.application.capability_provision.contracts import (
        InvestigationAnswer,
        InvestigationAnswerStatus,
    )
    from app.application.capability_provision.semantic_capability_support import (
        _apply_declared_answer,
    )

    terminal = _bound_attempt(root="PROC-0001")
    plan = _gates()._accept_semantic_investigation_plan(
        goal_class="read",
        comparison_requested=False,
        target_identities=[],
        evidence_needed=["90260921"],
        expected_delivery="record_detail",
        correlation="int2-partial-unmet",
    )
    declared = InvestigationAnswer(
        schema_version="1",
        status=InvestigationAnswerStatus.PARTIAL,
        answer="apenas uma página",
        evidence_refs=(0,),
    )
    result = _apply_declared_answer(
        terminal=terminal,
        declared_answer=declared,
        collected=(terminal,),
        plan=plan,
        correlation="int2-partial-unmet",
        unbound_outcome=None,
    )
    assert "declared_status_overridden" in result.limitations
    assert "coverage_unknown" not in result.limitations
