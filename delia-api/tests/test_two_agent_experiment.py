"""Two-Agent experimental variant (DELIA_TWO_AGENT_EXPERIMENT) — boundary
and recovery proofs for the Comprehension → Application → Investigation
split.

Variant B must prove, with the same governed machinery:

- the comprehension specialist's surface carries ONLY the typed goal
  declaration + clarification — never an owner tool;
- the investigation Agent in variant B never sees
  ``declare_investigation_goal`` — the objective reaches it exclusively
  through the Application-accepted plan seeded on shared deps;
- the Application acceptor (``_accept_semantic_investigation_plan``)
  remains the only validator: rejected proposals get the field-level
  feedback contract, bounded corrections, and never reach the owner;
- a comprehension failure/clarification before plan acceptance means
  ZERO owner calls and an honest terminal state;
- the plan accepted at the handoff is immutable (second declaration
  rejected), and the shared turn budget is composed — each agent gets a
  bounded share, never the full baseline limit;
- baseline A (flag off) keeps the single-toolset shape unchanged.
"""

from __future__ import annotations

from app.application.capability_provision.governed_capability_orchestrator import (
    OperationalCapabilityOrchestrator,
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
    ModelRequest,
    ModelResponse,
    ToolCallPart,
    ToolReturnPart,
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


def _gates(providers=None) -> OperationalCapabilityOrchestrator:
    return OperationalCapabilityOrchestrator(
        providers or _providers(),
        orchestration_instructions=load_test_orchestration_instructions(),
        invoke_model=InvokeModel(FakeProposalModel(())),
    )


def _final_answer() -> ModelResponse:
    return ModelResponse(
        parts=[
            ToolCallPart(
                "final_result",
                {
                    "schema_version": "1",
                    "status": "partial",
                    "answer": "done",
                    "evidence_refs": [],
                    "unmet_obligations": [],
                    "limitations": [],
                },
            )
        ]
    )


def _comp_outcome(status: str = "proposal_submitted") -> ModelResponse:
    return ModelResponse(
        parts=[
            ToolCallPart(
                "final_result",
                {"status": status, "note": ""},
            )
        ]
    )


def _read_call() -> ToolCallPart:
    return ToolCallPart(
        "alpha.search_items", {"arguments": {"query": "processos"}}
    )


def _valid_goal_call(**overrides) -> ToolCallPart:
    payload: dict = {
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
    }
    payload.update(overrides)
    return ToolCallPart("declare_investigation_goal", payload)


def _invalid_goal_call() -> ToolCallPart:
    return _valid_goal_call(
        evidence_needed=[
            {
                "description": "listagem",
                "evidence_source": "alpha.search_items",
                "operation": "read",
                "required_args": {"entity": "process", "action": "search"},
            }
        ]
    )


def _declare_returns(messages) -> list[dict]:
    out = []
    for m in messages:
        if not isinstance(m, ModelRequest):
            continue
        for part in m.parts:
            if (
                isinstance(part, ToolReturnPart)
                and part.tool_name == "declare_investigation_goal"
            ):
                out.append(part.content)
    return out


def _tool_names(info) -> set[str]:
    return {str(t.name) for t in info.function_tools}


def _is_comprehension(info) -> bool:
    names = _tool_names(info)
    return "declare_investigation_goal" in names and not any(
        "." in n for n in names
    )


def _spy_owner_calls(gates) -> list[str]:
    owner_calls: list[str] = []
    original = gates._governed_semantic_tool_invoke

    def _spy(**kwargs):
        owner_calls.append(str(kwargs.get("capability_id") or ""))
        return original(**kwargs)

    gates._governed_semantic_tool_invoke = _spy  # type: ignore[method-assign]
    return owner_calls


# -------------------------------------------------------------------
# Boundary: surfaces + governed handoff
# -------------------------------------------------------------------


def test_variant_b_surfaces_and_accepted_handoff():
    """B-B01: comprehension sees ONLY declare+clarify (no owner tools),
    investigation sees owner tools but NOT declare_investigation_goal;
    the accepted plan is echoed into the investigation prompt; the
    dependent READ then executes once through the governed path."""
    gates = _gates()
    owner_calls = _spy_owner_calls(gates)
    seen: dict = {"comp": None, "inv": None, "inv_prompt": ""}

    def _comp_fn(messages, _info):
        prior = sum(1 for m in messages if isinstance(m, ModelResponse))
        if prior == 0:
            return ModelResponse(parts=[_valid_goal_call()])
        return _comp_outcome()

    def _inv_fn(messages, _info):
        seen["inv_prompt"] = str(messages[0].parts[0].content)
        prior = sum(1 for m in messages if isinstance(m, ModelResponse))
        if prior == 0:
            return ModelResponse(parts=[_read_call()])
        return _final_answer()

    def _fn(messages, info):
        if _is_comprehension(info):
            seen["comp"] = _tool_names(info)
            return _comp_fn(messages, info)
        seen["inv"] = _tool_names(info)
        return _inv_fn(messages, info)

    engine = PydanticAiInvestigationOrchestrator(
        gates,
        model=FunctionModel(_fn),
        tool_calls_limit=8,
        two_agent_experiment=True,
    )
    with native_toolset_stub(alpha_beta_servers()):
        attempt = engine.attempt("liste os processos")

    assert seen["comp"] == {
        "declare_investigation_goal",
        "request_user_clarification",
    }
    assert seen["inv"] is not None
    assert "declare_investigation_goal" not in seen["inv"]
    assert "alpha.search_items" in seen["inv"]
    assert '"goal_class": "read"' in seen["inv_prompt"]
    assert '"expected_delivery": "enumeration"' in seen["inv_prompt"]
    assert owner_calls == ["alpha.search_items"]
    assert attempt.status is not None


def test_variant_b_rejected_proposal_corrects_with_field_feedback():
    """B-B02: a rejected comprehension proposal receives the SAME
    field-level INVALID_GOAL payload (invalid anchors, candidates) and
    a bounded correction is then accepted — the acceptor is shared."""
    gates = _gates()
    owner_calls = _spy_owner_calls(gates)
    comp_feedback: list = []

    def _comp_fn(messages, _info):
        comp_feedback.extend(_declare_returns(messages))
        prior = sum(1 for m in messages if isinstance(m, ModelResponse))
        if prior == 0:
            return ModelResponse(parts=[_invalid_goal_call()])
        if prior == 1:
            return ModelResponse(parts=[_valid_goal_call()])
        return _comp_outcome()

    def _inv_fn(messages, _info):
        prior = sum(1 for m in messages if isinstance(m, ModelResponse))
        if prior == 0:
            return ModelResponse(parts=[_read_call()])
        return _final_answer()

    def _fn(messages, info):
        if _is_comprehension(info):
            return _comp_fn(messages, info)
        return _inv_fn(messages, info)

    engine = PydanticAiInvestigationOrchestrator(
        gates,
        model=FunctionModel(_fn),
        tool_calls_limit=8,
        two_agent_experiment=True,
    )
    with native_toolset_stub(alpha_beta_servers()):
        engine.attempt("liste os processos")

    assert any(
        isinstance(item, str) and "INVALID_GOAL" in item
        for item in comp_feedback
    )
    assert owner_calls == ["alpha.search_items"]


def test_variant_b_second_declaration_blocked_plan_immutable():
    """B-B03: the accepted plan is immutable — a second declaration,
    even inside the comprehension run itself, is rejected by the SAME
    already-declared contract; investigation never re-declares."""
    gates = _gates()
    comp_feedback: list = []

    def _comp_fn(messages, _info):
        comp_feedback.extend(_declare_returns(messages))
        prior = sum(1 for m in messages if isinstance(m, ModelResponse))
        if prior == 0:
            return ModelResponse(parts=[_valid_goal_call()])
        if prior == 1:
            return ModelResponse(
                parts=[
                    _valid_goal_call(goal_class="analyze")
                ]
            )
        return _comp_outcome()

    def _inv_fn(messages, _info):
        prior = sum(1 for m in messages if isinstance(m, ModelResponse))
        if prior == 0:
            return ModelResponse(parts=[_read_call()])
        return _final_answer()

    def _fn(messages, info):
        if _is_comprehension(info):
            return _comp_fn(messages, info)
        return _inv_fn(messages, info)

    engine = PydanticAiInvestigationOrchestrator(
        gates,
        model=FunctionModel(_fn),
        tool_calls_limit=8,
        two_agent_experiment=True,
    )
    with native_toolset_stub(alpha_beta_servers()):
        engine.attempt("liste os processos")

    assert any(
        "investigation_goal_already_declared" in str(item)
        for item in comp_feedback
    )


# -------------------------------------------------------------------
# Recovery: handoff failure paths — zero owner calls, honest terminal
# -------------------------------------------------------------------


def test_variant_b_accepted_plan_clears_residual_clarification():
    """Accepted plan supersedes a residual comprehension clarification.

    Named identifier in the user turn suppresses the investigation
    auto-ask path, so a surviving residual would be the only source of
    ``CLARIFICATION_REQUIRED`` / the comprehension question text.
    """
    gates = _gates()
    owner_calls = _spy_owner_calls(gates)
    finalize_clarification: list[str | None] = []
    real_finalize = gates._finalize_semantic_investigation

    def _spy_finalize(**kwargs):
        finalize_clarification.append(kwargs.get("clarification_question"))
        return real_finalize(**kwargs)

    gates._finalize_semantic_investigation = _spy_finalize  # type: ignore[method-assign]

    def _comp_fn(messages, _info):
        prior = sum(1 for m in messages if isinstance(m, ModelResponse))
        if prior == 0:
            return ModelResponse(
                parts=[
                    _valid_goal_call(),
                    ToolCallPart(
                        "request_user_clarification",
                        {"question": "qual status residual?"},
                    ),
                ]
            )
        return _comp_outcome()

    def _inv_fn(messages, _info):
        prior = sum(1 for m in messages if isinstance(m, ModelResponse))
        if prior == 0:
            return ModelResponse(parts=[_read_call()])
        return _final_answer()

    def _fn(messages, info):
        if _is_comprehension(info):
            return _comp_fn(messages, info)
        return _inv_fn(messages, info)

    engine = PydanticAiInvestigationOrchestrator(
        gates,
        model=FunctionModel(_fn),
        tool_calls_limit=8,
        two_agent_experiment=True,
    )
    with native_toolset_stub(alpha_beta_servers()):
        attempt = engine.attempt("liste os processos PROC-0034")

    assert owner_calls == ["alpha.search_items"]
    assert finalize_clarification, "investigation must finalize"
    assert finalize_clarification[-1] in (None, "")
    assert "qual status residual?" not in (attempt.content or "")
    assert attempt.status is not GovernedCapabilityStatus.CLARIFICATION_REQUIRED


def test_variant_b_clarification_skips_investigation():
    """B-R01: a comprehension clarification with no accepted plan never
    starts the investigation run — zero owner calls and the honest
    CLARIFICATION terminal."""
    gates = _gates()
    owner_calls = _spy_owner_calls(gates)
    inv_ran = {"v": False}

    def _comp_fn(messages, _info):
        prior = sum(1 for m in messages if isinstance(m, ModelResponse))
        if prior == 0:
            return ModelResponse(
                parts=[
                    ToolCallPart(
                        "request_user_clarification",
                        {"question": "qual código?"},
                    )
                ]
            )
        return _comp_outcome("clarification_requested")

    def _inv_fn(messages, _info):
        inv_ran["v"] = True
        return _final_answer()

    def _fn(messages, info):
        if _is_comprehension(info):
            return _comp_fn(messages, info)
        return _inv_fn(messages, info)

    engine = PydanticAiInvestigationOrchestrator(
        gates,
        model=FunctionModel(_fn),
        tool_calls_limit=8,
        two_agent_experiment=True,
    )
    with native_toolset_stub(alpha_beta_servers()):
        attempt = engine.attempt("preciso do registro")

    assert inv_ran["v"] is False
    assert owner_calls == []
    assert attempt.status is GovernedCapabilityStatus.CLARIFICATION_REQUIRED


def test_variant_b_budget_exhaustion_zero_owner_calls():
    """B-R02: comprehension that never produces an acceptable plan
    exhausts its bounded request share (request_limit//3) — the
    investigation run never starts, zero owner calls, honest terminal
    with a typed handoff limitation."""
    gates = _gates()
    owner_calls = _spy_owner_calls(gates)
    comp_calls = {"n": 0}

    def _comp_fn(messages, _info):
        comp_calls["n"] += 1
        return ModelResponse(parts=[_invalid_goal_call()])

    def _inv_fn(messages, _info):
        raise AssertionError("investigation must never run")

    def _fn(messages, info):
        if _is_comprehension(info):
            return _comp_fn(messages, info)
        return _inv_fn(messages, info)

    engine = PydanticAiInvestigationOrchestrator(
        gates,
        model=FunctionModel(_fn),
        tool_calls_limit=8,
        request_limit=12,
        two_agent_experiment=True,
    )
    with native_toolset_stub(alpha_beta_servers()):
        attempt = engine.attempt("liste os processos")

    assert comp_calls["n"] <= 4  # request_limit//3 = 4
    assert owner_calls == []
    assert attempt.status is not GovernedCapabilityStatus.SUCCESS
    assert any(
        "comprehension_handoff=comprehension_budget_exhausted" in lim
        for lim in attempt.limitations
    )


def test_variant_b_accepted_plan_survives_post_acceptance_exhaustion():
    """B-R03: when the Application acceptor already validated the plan,
    exhausting the comprehension share on the observability-only
    outcome echo must NOT discard it — the authoritative artifact is
    ``deps.investigation_plan`` and the investigation run proceeds."""
    gates = _gates()
    owner_calls = _spy_owner_calls(gates)
    inv_calls = {"n": 0}

    def _comp_fn(messages, _info):
        # Keeps declaring past the accepted plan until the bounded
        # request share is exhausted — mimics the model not emitting
        # the end-of-run echo within budget (real-eval defect).
        return ModelResponse(parts=[_valid_goal_call()])

    def _inv_fn(messages, _info):
        inv_calls["n"] += 1
        prior = sum(1 for m in messages if isinstance(m, ModelResponse))
        if prior == 0:
            return ModelResponse(parts=[_read_call()])
        return _final_answer()

    def _fn(messages, info):
        if _is_comprehension(info):
            return _comp_fn(messages, info)
        return _inv_fn(messages, info)

    engine = PydanticAiInvestigationOrchestrator(
        gates,
        model=FunctionModel(_fn),
        tool_calls_limit=8,
        request_limit=12,
        two_agent_experiment=True,
    )
    with native_toolset_stub(alpha_beta_servers()):
        attempt = engine.attempt("liste os processos")

    assert inv_calls["n"] >= 1
    assert owner_calls == ["alpha.search_items"]
    assert not any(
        "comprehension_budget_exhausted" in lim
        for lim in attempt.limitations
    )


# -------------------------------------------------------------------
# Shared budget composition
# -------------------------------------------------------------------


def test_variant_b_shared_budget_composition():
    """B-C01: the turn budget is shared, not duplicated — comprehension
    gets a bounded request share (request_limit//3) and bounded tool
    calls (retries+2); investigation inherits the remaining requests
    and the shared deps.tool_calls counter."""
    import pydantic_ai.agent as _agent_mod

    gates = _gates()
    usage_limits_seen: list = []
    original = _agent_mod.Agent.run_sync

    def _spy(self, *args, **kwargs):
        usage_limits_seen.append(kwargs.get("usage_limits"))
        return original(self, *args, **kwargs)

    def _comp_fn(messages, _info):
        prior = sum(1 for m in messages if isinstance(m, ModelResponse))
        if prior == 0:
            return ModelResponse(parts=[_valid_goal_call()])
        return _comp_outcome()

    def _inv_fn(messages, _info):
        prior = sum(1 for m in messages if isinstance(m, ModelResponse))
        if prior == 0:
            return ModelResponse(parts=[_read_call()])
        return _final_answer()

    def _fn(messages, info):
        if _is_comprehension(info):
            return _comp_fn(messages, info)
        return _inv_fn(messages, info)

    _agent_mod.Agent.run_sync = _spy
    try:
        engine = PydanticAiInvestigationOrchestrator(
            gates,
            model=FunctionModel(_fn),
            request_limit=12,
            tool_calls_limit=8,
            agent_retries=1,
            two_agent_experiment=True,
        )
        with native_toolset_stub(alpha_beta_servers()):
            engine.attempt("liste os processos")
    finally:
        _agent_mod.Agent.run_sync = original

    assert len(usage_limits_seen) == 2
    comp_limits, inv_limits = usage_limits_seen
    assert comp_limits.request_limit == 4  # 12 // 3
    assert comp_limits.tool_calls_limit == 3  # retries + 2
    # comprehension consumed 2 requests (declare + final output) and 1
    # declared tool call — investigation inherits the remainder.
    assert inv_limits.request_limit == 10
    assert inv_limits.tool_calls_limit == 7


# -------------------------------------------------------------------
# Baseline A regression: flag OFF keeps the single toolset shape
# -------------------------------------------------------------------


def test_flag_off_baseline_single_toolset_unchanged():
    """A-R01: with the experiment flag OFF the single-Agent shape is
    unchanged — declare_investigation_goal remains on the investigation
    toolset alongside owner tools, and the R1 gate still blocks the
    dependent read until declaration."""
    gates = _gates()
    owner_calls = _spy_owner_calls(gates)
    seen_tools: set[str] = set()

    def _fn(messages, info):
        seen_tools.update(_tool_names(info))
        prior = sum(1 for m in messages if isinstance(m, ModelResponse))
        if prior == 0:
            return ModelResponse(parts=[_read_call()])
        if prior == 1:
            return ModelResponse(parts=[_valid_goal_call()])
        if prior == 2:
            return ModelResponse(parts=[_read_call()])
        return _final_answer()

    engine = PydanticAiInvestigationOrchestrator(
        gates, model=FunctionModel(_fn), tool_calls_limit=8
    )
    with native_toolset_stub(alpha_beta_servers()):
        engine.attempt("quais itens existem")

    assert "declare_investigation_goal" in seen_tools
    assert "alpha.search_items" in seen_tools
    assert owner_calls == ["alpha.search_items"]


# -------------------------------------------------------------------
# Shared turn budget — measured consumption and zero-balance
# -------------------------------------------------------------------


def test_variant_b_post_acceptance_exception_accounts_consumed_requests():
    """A02/A05/A12: comprehension accepts the plan, keeps consuming real
    provider requests on the observability echo, and then fails — the
    investigation request share MUST subtract the measured consumption.

    agent_retries=1 caps the comprehension share at
    min(retries+2, tool_calls_limit)=3 tool calls: after the accepted
    declaration, repeated declarations raise ``already_declared``; the
    run dies on its 4th request when that request's tool call is
    blocked — 4 real provider requests consumed.  The investigation leg
    must therefore inherit 12 - 4 = 8 requests — never the
    unaccounted 12.
    """
    import pydantic_ai.agent as _agent_mod

    gates = _gates()
    usage_limits_seen = []
    original = _agent_mod.Agent.run_sync

    def _spy(self, *args, **kwargs):
        usage_limits_seen.append(kwargs.get("usage_limits"))
        return original(self, *args, **kwargs)

    def _fn(messages, info):
        if _is_comprehension(info):
            return ModelResponse(parts=[_valid_goal_call()])
        return _final_answer()

    _agent_mod.Agent.run_sync = _spy
    try:
        engine = PydanticAiInvestigationOrchestrator(
            gates,
            model=FunctionModel(_fn),
            tool_calls_limit=8,
            request_limit=12,
            agent_retries=1,
            two_agent_experiment=True,
        )
        with native_toolset_stub(alpha_beta_servers()):
            engine.attempt("liste os processos")
    finally:
        _agent_mod.Agent.run_sync = original

    assert len(usage_limits_seen) == 2
    comp_limits, inv_limits = usage_limits_seen
    consumed_requests = 4  # 4th request's tool call blocked at share 3
    assert comp_limits.tool_calls_limit == 3
    assert inv_limits.request_limit == 12 - consumed_requests
    assert inv_limits.tool_calls_limit == 8 - 3


def test_variant_b_zero_remaining_request_budget_skips_investigation():
    """A10/A11: with a global request budget of 1, the comprehension
    share consumes it entirely; ``max(1, remaining)`` must not regrant
    a request — the investigation leg cannot start, and zero owner
    calls happen.
    """
    gates = _gates()
    inv_calls = {"n": 0}
    owner_calls = _spy_owner_calls(gates)

    def _fn(messages, info):
        if _is_comprehension(info):
            return ModelResponse(parts=[_valid_goal_call()])
        inv_calls["n"] += 1
        return _final_answer()

    engine = PydanticAiInvestigationOrchestrator(
        gates,
        model=FunctionModel(_fn),
        tool_calls_limit=8,
        request_limit=1,
        agent_retries=1,
        two_agent_experiment=True,
    )
    with native_toolset_stub(alpha_beta_servers()):
        attempt = engine.attempt("liste os processos")

    assert inv_calls["n"] == 0
    assert owner_calls == []
    assert attempt.status is not GovernedCapabilityStatus.SUCCESS


def test_variant_b_zero_remaining_tool_budget_skips_investigation():
    """A11/A12: tool_calls_limit=1 is fully consumed by the accepted
    comprehension declaration — the shared counter reaches the global
    cap, so the investigation leg receives no tool-call regrant.
    """
    gates = _gates()
    inv_calls = {"n": 0}
    owner_calls = _spy_owner_calls(gates)

    def _fn(messages, info):
        if _is_comprehension(info):
            prior = sum(1 for m in messages if isinstance(m, ModelResponse))
            if prior == 0:
                return ModelResponse(parts=[_valid_goal_call()])
            return _comp_outcome()
        inv_calls["n"] += 1
        return _final_answer()

    engine = PydanticAiInvestigationOrchestrator(
        gates,
        model=FunctionModel(_fn),
        tool_calls_limit=1,
        request_limit=12,
        agent_retries=1,
        two_agent_experiment=True,
    )
    with native_toolset_stub(alpha_beta_servers()):
        attempt = engine.attempt("liste os processos")

    assert inv_calls["n"] == 0
    assert owner_calls == []
    assert attempt.status is not GovernedCapabilityStatus.SUCCESS


def test_variant_b_post_acceptance_exception_class_neutral_accounting():
    """A05/A08/A09: whatever non-terminal class kills the observability
    echo AFTER the plan was accepted — UnexpectedModelBehavior, provider
    or generic errors — the artifact is kept, the measured consumption
    is subtracted, and no extra budget is granted.
    """
    import pydantic_ai.agent as _agent_mod
    from pydantic_ai.exceptions import UnexpectedModelBehavior

    for exc_type in (UnexpectedModelBehavior, RuntimeError):
        gates = _gates()
        usage_limits_seen = []
        original = _agent_mod.Agent.run_sync

        def _spy(self, *args, **kwargs):
            usage_limits_seen.append(kwargs.get("usage_limits"))
            return original(self, *args, **kwargs)

        raised = {"done": False}

        def _fn(messages, info):
            if _is_comprehension(info):
                prior = sum(
                    1 for m in messages if isinstance(m, ModelResponse)
                )
                if prior == 0:
                    return ModelResponse(parts=[_valid_goal_call()])
                if not raised["done"]:
                    raised["done"] = True
                    raise exc_type("echo failed")
                return _comp_outcome()
            return _final_answer()

        _agent_mod.Agent.run_sync = _spy
        try:
            engine = PydanticAiInvestigationOrchestrator(
                gates,
                model=FunctionModel(_fn),
                tool_calls_limit=8,
                request_limit=12,
                agent_retries=1,
                two_agent_experiment=True,
            )
            with native_toolset_stub(alpha_beta_servers()):
                attempt = engine.attempt("liste os processos")
        finally:
            _agent_mod.Agent.run_sync = original

        assert len(usage_limits_seen) == 2, exc_type
        _, inv_limits = usage_limits_seen
        # One completed provider request (the accepted declaration)
        # was consumed before the echo request failed mid-flight —
        # matching the framework's own usage.requests semantics, the
        # failed request is unmeasured but the completed one must be
        # subtracted, never presumed zero.
        assert inv_limits.request_limit == 11, exc_type
        assert inv_limits.tool_calls_limit == 7, exc_type


def test_variant_b_terminal_exception_propagates_from_comprehension():
    """A06/A07: deadline/cancel/turn-budget failures are terminal —
    they propagate out of the comprehension pass to the owning
    turn-budget boundary (PROCESSING_TIMEOUT), never swallowed into a
    kept artifact or an honest insufficient.
    """
    from app.application.capability_provision.semantic_capability_support import (
        _StageDeadlineExceeded,
    )

    gates = _gates()
    inv_calls = {"n": 0}

    def _fn(messages, info):
        if _is_comprehension(info):
            raise _StageDeadlineExceeded("stage deadline")
        inv_calls["n"] += 1
        return _final_answer()

    engine = PydanticAiInvestigationOrchestrator(
        gates,
        model=FunctionModel(_fn),
        tool_calls_limit=8,
        request_limit=12,
        agent_retries=1,
        two_agent_experiment=True,
    )
    with native_toolset_stub(alpha_beta_servers()):
        attempt = engine.attempt("liste os processos")

    assert attempt.status is GovernedCapabilityStatus.PROCESSING_TIMEOUT
    assert inv_calls["n"] == 0
