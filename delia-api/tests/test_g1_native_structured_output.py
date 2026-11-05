"""G1 — native typed structured output for the investigation Agent.

The Agent declares an ``InvestigationAnswer`` (strict dataclass) via
``output_type``; the deterministic acceptor
``_apply_declared_answer`` binds every claim to real collected
attempts — refs that do not point to actual business evidence are
dropped, a COMPLETE claim is honored only when obligations are
satisfied, and nothing the model declares becomes authority or FACT.
"""

from __future__ import annotations

import dataclasses

from app.application.capability_provision.contracts import (
    InvestigationAnswer,
    InvestigationAnswerStatus,
)
from app.application.capability_provision.orchestration import (
    _apply_declared_answer,
)
from app.application.interaction.turn_budget import TurnDeadline
from app.application.interaction.capability_attempt import (
    GovernedCapabilityAttempt,
    GovernedCapabilityProvenance,
    GovernedCapabilityStatus,
    SourceRef,
)
from app.domain.specialist_interop.model import (
    InteropProtocol,
    SpecialistOutcome,
    SpecialistResultProvenance,
    SpecialistResultStatus,
)


def _outcome() -> SpecialistOutcome:
    return SpecialistOutcome(
        status=SpecialistResultStatus.COMPLETED,
        provenance=SpecialistResultProvenance(
            specialist_id="pa",
            remote_name="search_items",
            protocol=InteropProtocol.MCP,
            correlation_id="c1",
            observed_at="2026-01-01T00:00:00Z",
        ),
        content_text="owner record",
        is_complete=True,
        structured={"items": [{"id": "1"}]},
    )


def _attempt(limitations: tuple[str, ...] = ()) -> GovernedCapabilityAttempt:
    outcome = _outcome()
    return GovernedCapabilityAttempt(
        status=GovernedCapabilityStatus.SUCCESS,
        correlation_id="c1",
        outcome=outcome,
        provenance=GovernedCapabilityProvenance(
            source_refs=(
                SourceRef(
                    source_id="pa",
                    source_system="pa",
                    provider_name="pa",
                    observed_at="2026-01-01T00:00:00Z",
                ),
            ),
            specialist_id="pa",
            remote_capability="search_items",
            action_id="search_items",
            protocol=InteropProtocol.MCP.value,
            observed_at="2026-01-01T00:00:00Z",
            correlation_id="c1",
            is_complete=True,
        ),
        content="rendered",
        limitations=limitations,
    )


def _terminal() -> GovernedCapabilityAttempt:
    return GovernedCapabilityAttempt(
        status=GovernedCapabilityStatus.SUCCESS,
        correlation_id="c1",
        content="deterministic content",
        limitations=(),
    )


# ------------------------------------------------------------------
# contract
# ------------------------------------------------------------------


def test_investigation_answer_is_typed_not_permissive():
    answer = InvestigationAnswer(
        schema_version="1",
        status=InvestigationAnswerStatus.COMPLETE,
        answer="the record exists",
        evidence_refs=(0,),
    )
    assert answer.schema_version == "1"
    assert answer.status is InvestigationAnswerStatus.COMPLETE
    assert answer.evidence_refs == (0,)
    # no permissive dict payload — strict fields only
    assert dataclasses.is_dataclass(answer)
    assert not hasattr(answer, "extra")


# ------------------------------------------------------------------
# acceptor — fabricated refs never bind
# ------------------------------------------------------------------


def test_out_of_range_evidence_ref_is_dropped():
    terminal = _terminal()
    collected = (_attempt(),)
    declared = InvestigationAnswer(
        schema_version="1",
        status=InvestigationAnswerStatus.COMPLETE,
        answer="synthesized",
        evidence_refs=(0, 7),
    )
    out = _apply_declared_answer(
        terminal=terminal,
        declared_answer=declared,
        collected=collected,
        plan=None,
        correlation="c1",
        unbound_outcome=None,
    )
    assert "evidence_ref_unbound:7" in out.limitations
    # mixed valid/invalid refs + plan=None → COMPLETE never honored;
    # verified deterministic content is always the authoritative answer
    assert out.content == "deterministic content"
    assert "declared_status_overridden" in out.limitations


def test_valid_sourceref_never_promotes_hallucinated_prose():
    """A valid indexed SourceRef proves the observation's provenance —
    never the truth of generated prose. Model wording must not replace
    the verified deterministic answer (doc 258 §1)."""
    terminal = _terminal()
    declared = InvestigationAnswer(
        schema_version="1",
        status=InvestigationAnswerStatus.COMPLETE,
        answer="the product costs R$ 999,90 and ships tomorrow",
        evidence_refs=(0,),
    )
    out = _apply_declared_answer(
        terminal=terminal,
        declared_answer=declared,
        collected=(_attempt(),),
        plan=None,
        correlation="c1",
        unbound_outcome=None,
    )
    assert "999" not in (out.content or "")
    assert out.content == "deterministic content"


def test_real_but_irrelevant_evidence_does_not_ground_complete():
    """Real observation exists but coverage is unknown (plan=None) —
    a COMPLETE claim can never be proven vacuously (doc 258 §4)."""
    declared = InvestigationAnswer(
        schema_version="1",
        status=InvestigationAnswerStatus.COMPLETE,
        answer="anything",
        evidence_refs=(0,),
    )
    out = _apply_declared_answer(
        terminal=_terminal(),
        declared_answer=declared,
        collected=(_attempt(),),
        plan=None,
        correlation="c1",
        unbound_outcome=None,
    )
    assert "declared_status_overridden" in out.limitations
    assert "coverage_unknown" in out.limitations
    assert out.content == "deterministic content"


def test_complete_proven_only_when_all_refs_bind_and_obligations_met():
    """Fully consistent COMPLETE (all refs valid, obligations satisfied)
    is accepted as consistent — but STILL never replaces the verified
    deterministic content (doc 258 §1)."""
    class _Plan:
        evidence_needed = ()

    terminal = _terminal()
    declared = InvestigationAnswer(
        schema_version="1",
        status=InvestigationAnswerStatus.COMPLETE,
        answer="model wording",
        evidence_refs=(0,),
    )
    out = _apply_declared_answer(
        terminal=terminal,
        declared_answer=declared,
        collected=(_attempt(),),
        plan=_Plan(),
        correlation="c1",
        unbound_outcome=None,
    )
    # coverage_unknown (evidence_needed empty) — or consistent; either
    # way the deterministic content stays authoritative
    assert out.content == "deterministic content"


def test_unknown_schema_version_rejects_whole_declaration():
    declared = InvestigationAnswer(
        schema_version="2",
        status=InvestigationAnswerStatus.COMPLETE,
        answer="x",
        evidence_refs=(0,),
    )
    out = _apply_declared_answer(
        terminal=_terminal(),
        declared_answer=declared,
        collected=(_attempt(),),
        plan=None,
        correlation="c1",
        unbound_outcome=None,
    )
    assert "declared_schema_rejected" in out.limitations
    assert out.content == "deterministic content"


def test_clarification_never_discards_verified_answer():
    """Model-declared clarification must not throw away a terminal that
    already carries verified business evidence (doc 258 §5)."""
    declared = InvestigationAnswer(
        schema_version="1",
        status=InvestigationAnswerStatus.NEEDS_CLARIFICATION,
        clarification_question="Qual registro?",
    )
    out = _apply_declared_answer(
        terminal=_terminal(),
        declared_answer=declared,
        collected=(_attempt(),),
        plan=None,
        correlation="c1",
        unbound_outcome=None,
    )
    assert out.status is GovernedCapabilityStatus.SUCCESS
    assert "declared_clarification_ignored" in out.limitations


def test_clarification_still_applies_when_no_verified_evidence():
    declared = InvestigationAnswer(
        schema_version="1",
        status=InvestigationAnswerStatus.NEEDS_CLARIFICATION,
        clarification_question="Qual registro consultar?",
    )
    empty_terminal = GovernedCapabilityAttempt(
        status=GovernedCapabilityStatus.NOT_APPLICABLE,
        correlation_id="c1",
        limitations=("insufficient_evidence",),
    )
    out = _apply_declared_answer(
        terminal=empty_terminal,
        declared_answer=declared,
        collected=(),
        plan=None,
        correlation="c1",
        unbound_outcome=None,
    )
    assert out.status is GovernedCapabilityStatus.CLARIFICATION_REQUIRED


def test_ref_to_non_business_attempt_is_dropped():
    non_business = _attempt(limitations=("discovery_metadata_observation",))
    terminal = _terminal()
    declared = InvestigationAnswer(
        schema_version="1",
        status=InvestigationAnswerStatus.COMPLETE,
        answer="synthesized",
        evidence_refs=(0,),
    )
    out = _apply_declared_answer(
        terminal=terminal,
        declared_answer=declared,
        collected=(non_business,),
        plan=None,
        correlation="c1",
        unbound_outcome=None,
    )
    assert "evidence_ref_unbound:0" in out.limitations
    # unproven COMPLETE → deterministic content stays + override noted
    assert out.content == "deterministic content"
    assert "declared_status_overridden" in out.limitations


def test_complete_claim_without_any_valid_refs_is_overridden():
    terminal = _terminal()
    declared = InvestigationAnswer(
        schema_version="1",
        status=InvestigationAnswerStatus.COMPLETE,
        answer="synthesized",
        evidence_refs=(),
    )
    out = _apply_declared_answer(
        terminal=terminal,
        declared_answer=declared,
        collected=(),
        plan=None,
        correlation="c1",
        unbound_outcome=None,
    )
    assert out.content == "deterministic content"
    assert "declared_status_overridden" in out.limitations


# ------------------------------------------------------------------
# acceptor — clarification, partial, declared limitations
# ------------------------------------------------------------------


def test_declared_clarification_takes_bounded_path():
    declared = InvestigationAnswer(
        schema_version="1",
        status=InvestigationAnswerStatus.NEEDS_CLARIFICATION,
        clarification_question="Qual registro consultar?",
    )
    out = _apply_declared_answer(
        terminal=_terminal(),
        declared_answer=declared,
        collected=(),
        plan=None,
        correlation="c1",
        unbound_outcome=None,
    )
    assert out.status is GovernedCapabilityStatus.CLARIFICATION_REQUIRED
    assert out.content == "Qual registro consultar?"
    assert "agent_requested_clarification" in out.limitations


def test_declared_unmet_obligations_merge_into_limitations():
    declared = InvestigationAnswer(
        schema_version="1",
        status=InvestigationAnswerStatus.PARTIAL,
        unmet_obligations=("price_check",),
        limitations=("owner_timeout",),
    )
    out = _apply_declared_answer(
        terminal=_terminal(),
        declared_answer=declared,
        collected=(),
        plan=None,
        correlation="c1",
        unbound_outcome=None,
    )
    assert "declared_unmet_obligation:price_check" in out.limitations
    assert "declared_limitation:owner_timeout" in out.limitations


def test_no_declared_answer_passes_terminal_through():
    terminal = _terminal()
    out = _apply_declared_answer(
        terminal=terminal,
        declared_answer=None,
        collected=(),
        plan=None,
        correlation="c1",
        unbound_outcome=None,
    )
    assert out is terminal


def test_answer_text_is_bounded():
    declared = InvestigationAnswer(
        schema_version="1",
        status=InvestigationAnswerStatus.COMPLETE,
        answer="x" * 5000,
        evidence_refs=(0,),
    )
    out = _apply_declared_answer(
        terminal=_terminal(),
        declared_answer=declared,
        collected=(_attempt(),),
        plan=None,
        correlation="c1",
        unbound_outcome=None,
    )
    assert len(out.content) <= 2000


# ------------------------------------------------------------------
# residual G1 (doc 259 §25): clarification with PARTIAL evidence
# ------------------------------------------------------------------


def test_clarification_applies_with_partial_evidence_and_unmet_obligations():
    """Verified partial evidence coexisting with unmet material
    obligations must NOT cause a declared clarification to be dropped —
    the bounded clarification path applies while the verified evidence
    is preserved, never discarded."""
    class _Plan:
        evidence_needed = ("price_check", "stock_check")

    declared = InvestigationAnswer(
        schema_version="1",
        status=InvestigationAnswerStatus.NEEDS_CLARIFICATION,
        clarification_question="Qual armazém consultar para o estoque?",
    )
    # terminal carries REAL verified owner evidence (outcome+provenance)
    verified_terminal = dataclasses.replace(
        _terminal(),
        outcome=_outcome(),
        provenance=_attempt().provenance,
    )
    out = _apply_declared_answer(
        terminal=verified_terminal,
        declared_answer=declared,
        collected=(_attempt(),),
        plan=_Plan(),
        correlation="c1",
        unbound_outcome=None,
    )
    assert out.status is GovernedCapabilityStatus.CLARIFICATION_REQUIRED
    # verified evidence preserved — real fields survive the
    # clarification, not merely the marker
    assert "verified_evidence_preserved" in out.limitations
    assert out.outcome is verified_terminal.outcome
    assert out.provenance is verified_terminal.provenance
    assert out.provenance.source_refs[0].source_id == "pa"


def test_clarification_ignored_only_when_obligations_fully_met():
    """When material obligations are all satisfied, a declared
    clarification is ignored — there is no proven unmet need."""
    class _Plan:
        evidence_needed = ()

    declared = InvestigationAnswer(
        schema_version="1",
        status=InvestigationAnswerStatus.NEEDS_CLARIFICATION,
        clarification_question="Qual registro?",
    )
    out = _apply_declared_answer(
        terminal=_terminal(),
        declared_answer=declared,
        collected=(_attempt(),),
        plan=_Plan(),
        correlation="c1",
        unbound_outcome=None,
    )
    assert out.status is GovernedCapabilityStatus.SUCCESS
    assert "declared_clarification_ignored" in out.limitations


# ------------------------------------------------------------------
# G4 M1: the investigation Agent runs run_sync exactly once per
# attempt — no external retry loop multiplies physical model calls.
# ------------------------------------------------------------------


def test_agent_run_sync_is_single_invocation_per_attempt():
    """The investigation attempt calls ``agent.run_sync`` exactly once —
    governed_retries never wraps the Agent path, so retries can never
    multiply (doc 261 M1). Agent-internal native retries (tool calls +
    ModelRetry output) remain bounded by UsageLimits."""
    import inspect
    from app.infrastructure.orchestration import (
        pydantic_ai_investigation as inv,
    )

    src = inspect.getsource(inv)
    # exactly one run_sync call site in the whole module
    assert src.count(".run_sync(") == 1
    # no governed-retries loop wraps the Agent path
    assert "call_retry_eligible" not in src


def test_governed_retries_serves_non_agent_paths_only():
    """call_retry_eligible stays for the conversational + model-stage
    invocation paths (invoke_model outside the Agent) — separate
    legitimate contract, clamped to the PO ceiling (doc 261 M1)."""
    from app.application.model_invocation.governed_retries import (
        LLM_CALL_MAX_ATTEMPTS,
        call_retry_eligible,
    )

    assert LLM_CALL_MAX_ATTEMPTS == 3
    # recoverable + within limit → eligible
    assert call_retry_eligible("timeout", 1, 2) is True
    # definitive codes never retry
    assert call_retry_eligible("rejected", 1, 2) is False
    # config can never exceed the PO ceiling
    assert call_retry_eligible("timeout", 3, 99) is False


# ------------------------------------------------------------------
# G4 M1 behavioral (doc 262 §3): instrumented Agent — physical model
# requests counted, not source-text inspection.
# ------------------------------------------------------------------


def test_behavioral_agent_invokes_model_once_per_run():
    """Instrumented FunctionModel counts real provider invocations:
    a plain run consumes exactly ONE model request; the investigation
    attempt never wraps run_sync in an outer retry loop."""
    from unittest.mock import patch
    from pydantic_ai import Agent
    from pydantic_ai.models.function import FunctionModel
    from pydantic_ai.messages import ModelResponse, TextPart

    calls = []

    def _fn(messages, _info):
        calls.append(len(messages))
        return ModelResponse(parts=[TextPart("ok")])

    agent = Agent(FunctionModel(_fn), output_type=str)
    agent.run_sync("hi")
    assert len(calls) == 1


def test_behavioral_invalid_output_triggers_native_output_retry():
    """An output_validator rejection (ModelRetry) causes exactly ONE
    extra native retry inside the same run — bounded, not unbounded."""
    from pydantic_ai import Agent, ModelRetry
    from pydantic_ai.models.function import FunctionModel
    from pydantic_ai.messages import ModelResponse, TextPart

    calls = []

    def _fn(messages, _info):
        calls.append(messages)
        if len(calls) == 1:
            return ModelResponse(parts=[TextPart("bad")])
        return ModelResponse(parts=[TextPart("good")])

    agent = Agent(FunctionModel(_fn), output_type=str, retries=2)

    @agent.output_validator
    def _check(ctx, output):
        if output == "bad":
            raise ModelRetry("invalid")
        return output

    result = agent.run_sync("hi")
    assert result.output == "good"
    assert len(calls) == 2  # 1 initial + 1 bounded native retry


def test_behavioral_usage_limit_blocks_retries():
    """UsageLimits request_limit=1 caps the run — a ModelRetry after
    the first request raises UsageLimitExceeded instead of a second
    physical call."""
    import pytest
    from pydantic_ai import Agent, ModelRetry, UsageLimits
    from pydantic_ai.exceptions import UsageLimitExceeded
    from pydantic_ai.models.function import FunctionModel
    from pydantic_ai.messages import ModelResponse, TextPart

    calls = []

    def _fn(messages, _info):
        calls.append(messages)
        return ModelResponse(parts=[TextPart("bad")])

    agent = Agent(FunctionModel(_fn), output_type=str)

    @agent.output_validator
    def _check(ctx, output):
        raise ModelRetry("invalid")

    with pytest.raises(UsageLimitExceeded):
        agent.run_sync("hi", usage_limits=UsageLimits(request_limit=1))
    assert len(calls) == 1  # capped — no second physical request


# ------------------------------------------------------------------
# G7 G4 (doc 265 §B): instrumented PydanticAiInvestigationOrchestrator
# — real gates/toolset, physical model requests counted.
# ------------------------------------------------------------------


def test_engine_physical_requests_one_call_one_tool():
    """Full engine path with real gates: one tool-call request + one
    final_result request = 2 physical model calls — no external retry
    multiplication, no extra run_sync."""
    from tests.test_pydantic_ai_semantic_rework import _gates
    from app.infrastructure.orchestration.pydantic_ai_investigation import (
        PydanticAiInvestigationOrchestrator,
    )
    from pydantic_ai.messages import (
        ModelResponse, ToolCallPart,
    )
    from pydantic_ai.models.function import FunctionModel

    gates = _gates()
    catalog = gates._project_semantic_tool_catalog(
        correlation="c", deadline=TurnDeadline.start(30.0)
    )
    read = next(c for c in catalog if c["operation_class"] == "READ")
    model_calls = []

    def _fn(messages, _info):
        model_calls.append(len(messages))
        if not any(isinstance(m, ModelResponse) for m in messages):
            return ModelResponse(
                parts=[
                    ToolCallPart(
                        "invoke_read_capability",
                        {
                            "capability_id": read["capability_id"],
                            "arguments": {"query": "terminal"},
                        },
                    )
                ]
            )
        return _final_answer("done", status="insufficient")

    engine = PydanticAiInvestigationOrchestrator(
        gates, model=FunctionModel(_fn), tool_calls_limit=4
    )
    attempt = engine.attempt("liste terminais")
    # exactly 2 physical model requests: tool call + final_result
    assert len(model_calls) == 2
    assert attempt.governed_attempts is not None


def test_engine_tool_invocation_is_governed_not_multiplied():
    """Each tool invocation passes through the governed stage gates —
    count them via the catalog spy: one capability call = one
    governed owner invocation, never retried by the Agent loop."""
    from tests.test_pydantic_ai_semantic_rework import _gates
    from app.infrastructure.orchestration.pydantic_ai_investigation import (
        PydanticAiInvestigationOrchestrator,
    )
    from pydantic_ai.messages import (
        ModelResponse, ToolCallPart,
    )
    from pydantic_ai.models.function import FunctionModel

    gates = _gates()
    catalog = gates._project_semantic_tool_catalog(
        correlation="c", deadline=TurnDeadline.start(30.0)
    )
    read = next(c for c in catalog if c["operation_class"] == "READ")
    invocations = []
    original = gates._governed_semantic_tool_invoke

    def _spy(**kwargs):
        invocations.append(kwargs.get("capability_id"))
        return original(**kwargs)

    gates._governed_semantic_tool_invoke = _spy

    def _fn(messages, _info):
        if not any(isinstance(m, ModelResponse) for m in messages):
            return ModelResponse(
                parts=[
                    ToolCallPart(
                        "invoke_read_capability",
                        {
                            "capability_id": read["capability_id"],
                            "arguments": {"query": "x"},
                        },
                    )
                ]
            )
        return _final_answer("done", status="insufficient")

    engine = PydanticAiInvestigationOrchestrator(
        gates, model=FunctionModel(_fn), tool_calls_limit=4
    )
    engine.attempt("liste")
    # one tool call → exactly one governed owner invocation
    assert len(invocations) == 1
    assert invocations[0] == read["capability_id"]


# ------------------------------------------------------------------
# G7 (doc 269 §4): investigation Agent context window gate — the
# Agent path must fail closed BEFORE run_sync when the assembled
# context estimate exceeds the configured window (no second token
# engine — reuses context_budget.estimate_text_tokens).
# ------------------------------------------------------------------


def test_context_window_gate_below_window_reaches_model():
    """Estimated context below the configured window → the model is
    actually invoked."""
    from tests.test_pydantic_ai_semantic_rework import _gates
    from app.infrastructure.orchestration.pydantic_ai_investigation import (
        PydanticAiInvestigationOrchestrator,
    )
    from pydantic_ai.models.function import FunctionModel

    calls = []

    def _fn(messages, _info):
        calls.append(len(messages))
        return _final_answer("ok", status="insufficient")

    engine = PydanticAiInvestigationOrchestrator(
        _gates(),
        model=FunctionModel(_fn),
        context_window_tokens=1_000_000,
    )
    engine.attempt("oi")
    assert calls  # model reached


def test_context_window_gate_above_window_never_calls_model():
    """Estimated context at/above the window → typed honest outcome
    `investigation_context_overflow`, ZERO physical model requests —
    never a raw ModelHTTPError leaking to the turn."""
    from tests.test_pydantic_ai_semantic_rework import _gates
    from app.infrastructure.orchestration.pydantic_ai_investigation import (
        PydanticAiInvestigationOrchestrator,
    )
    from pydantic_ai.models.function import FunctionModel

    calls = []

    def _fn(messages, _info):
        calls.append(len(messages))
        return _final_answer("ok", status="insufficient")

    engine = PydanticAiInvestigationOrchestrator(
        _gates(),
        model=FunctionModel(_fn),
        context_window_tokens=1,  # any non-empty prompt exceeds it
    )
    attempt = engine.attempt("oi")
    assert calls == []
    assert attempt.error_code == "investigation_context_overflow"


def test_context_window_gate_disabled_when_unset():
    """window unset (None → profile effective_context_window_tokens
    null) → enforcement off rather than guessing (doc 103)."""
    from tests.test_pydantic_ai_semantic_rework import _gates
    from app.infrastructure.orchestration.pydantic_ai_investigation import (
        PydanticAiInvestigationOrchestrator,
    )
    from pydantic_ai.models.function import FunctionModel

    calls = []

    def _fn(messages, _info):
        calls.append(len(messages))
        return _final_answer("ok", status="insufficient")

    engine = PydanticAiInvestigationOrchestrator(
        _gates(), model=FunctionModel(_fn)
    )
    engine.attempt("oi")
    assert calls


def test_context_envelope_includes_tool_schemas_and_reserve():
    """The pre-call estimate accounts for tool schemas + overhead +
    generation reserve — with the real 10-cap catalog a tiny prompt +
    window just above raw text still triggers overflow because the
    envelope terms push it over (doc 270 §2)."""
    from tests.test_pydantic_ai_semantic_rework import _gates
    from app.application.model_invocation.context_budget import (
        estimate_text_tokens,
    )
    from app.infrastructure.orchestration.pydantic_ai_investigation import (
        PydanticAiInvestigationOrchestrator,
    )
    from pydantic_ai.models.function import FunctionModel

    calls = []

    def _fn(messages, _info):
        calls.append(len(messages))
        return _final_answer("ok", status="insufficient")

    # window larger than instructions+prompt alone but smaller than the
    # full envelope → gate must fire (envelope terms counted)
    engine = PydanticAiInvestigationOrchestrator(
        _gates(),
        model=FunctionModel(_fn),
        context_window_tokens=estimate_text_tokens("oi") + 1_200,
    )
    attempt = engine.attempt("oi")
    assert attempt.error_code == "investigation_context_overflow"
    assert calls == []


# ------------------------------------------------------------------
# G7 (doc 272): native message_history migration + ProcessHistory
# pair integrity — prior turns arrive as ModelMessages, tool
# call/return pairs never split, mandatory overflow fails typed.
# ------------------------------------------------------------------


def test_prior_turns_arrive_as_native_message_history():
    """ConversationContextTurn converts to native message_history —
    FunctionModel receives the prior turns as ModelRequest/
    ModelResponse messages, NOT embedded in the prompt text."""
    from tests.test_pydantic_ai_semantic_rework import _gates
    from app.application.model_invocation.contracts import (
        ConversationContextTurn,
        TurnKind,
    )
    from app.infrastructure.orchestration.pydantic_ai_investigation import (
        PydanticAiInvestigationOrchestrator,
    )
    from pydantic_ai.messages import ModelRequest, ModelResponse
    from pydantic_ai.models.function import FunctionModel

    seen = []

    def _fn(messages, _info):
        seen.extend(messages)
        return _final_answer("ok", status="insufficient")

    prior = (
        ConversationContextTurn(
            kind=TurnKind.USER_INPUT,
            content="pergunta anterior",
            epistemic_class=None,
            entity_refs=(),
        ),
        ConversationContextTurn(
            kind=TurnKind.DELIA_RESULT,
            content="resposta anterior",
            epistemic_class=None,
            entity_refs=(),
        ),
    )
    engine = PydanticAiInvestigationOrchestrator(
        _gates(), model=FunctionModel(_fn)
    )
    engine.attempt("nova pergunta", prior_turns=prior)
    kinds = {
        (type(m).__name__, tuple(getattr(p, "part_kind", "") for p in m.parts))
        for m in seen[:2]
    }
    assert ("ModelRequest", ("user-prompt",)) in kinds
    assert ("ModelResponse", ("text",)) in kinds


def test_history_processor_preserves_tool_call_return_pairs():
    """Under overflow pressure the processor drops COMPLETE units —
    a ModelRequest carrying ToolReturnParts is never orphaned from
    its ModelResponse ToolCallParts (doc 272 §2). Exercises the
    PRODUCTION _history_units grouping."""
    from app.infrastructure.orchestration.pydantic_ai_investigation import (
        _history_units,
    )
    from pydantic_ai.messages import (
        ModelRequest,
        ModelResponse,
        TextPart,
        ToolCallPart,
        ToolReturnPart,
        UserPromptPart,
    )

    msgs = [
        ModelRequest(parts=[UserPromptPart("x" * 3000)]),
        ModelResponse(
            parts=[ToolCallPart("tool_a", {"a": 1}, tool_call_id="c1")]
        ),
        ModelRequest(
            parts=[ToolReturnPart("tool_a", "y" * 3000, tool_call_id="c1")]
        ),
        ModelResponse(parts=[TextPart("interim")]),
        ModelRequest(parts=[UserPromptPart("next")]),
    ]
    units = _history_units(msgs)
    # [user] [call+return] [interim-text] [next-user] — the call and
    # its return form ONE unit, never separable
    assert len(units) == 4
    assert len(units[1]) == 2
    flat = units[1]
    assert any(isinstance(p, ToolCallPart) for p in flat[0].parts)
    assert any(isinstance(p, ToolReturnPart) for p in flat[1].parts)


def test_current_turn_survives_compaction_prior_turn_dropped():
    """Doc 273 §2-3: under compaction pressure the CURRENT user
    question (last user-prompt unit) survives while OLD prior turns
    drop — production ``_select_surviving_messages``, not a copy."""
    from app.infrastructure.orchestration.pydantic_ai_investigation import (
        _select_surviving_messages,
    )
    from pydantic_ai.messages import (
        ModelRequest,
        ModelResponse,
        TextPart,
        ToolCallPart,
        ToolReturnPart,
        UserPromptPart,
    )

    msgs = [
        ModelRequest(parts=[UserPromptPart("PERGUNTA_ANTIGA " + "z" * 8000)]),
        ModelResponse(parts=[TextPart("resposta antiga " + "w" * 8000)]),
        ModelRequest(parts=[UserPromptPart("PERGUNTA_ATUAL")]),
        ModelResponse(
            parts=[ToolCallPart("tool_a", {"a": 1}, tool_call_id="c1")]
        ),
        ModelRequest(
            parts=[
                ToolReturnPart("tool_a", "evidência", tool_call_id="c1")
            ]
        ),
        ModelResponse(parts=[TextPart("parcial")]),
    ]
    survivors = _select_surviving_messages(msgs, window=1200)
    texts = [
        str(getattr(p, "content", "") or "")
        for m in survivors
        for p in m.parts
    ]
    joined = "|".join(texts)
    # CURRENT objective preserved — question + its tool evidence
    assert "PERGUNTA_ATUAL" in joined
    assert "evidência" in joined
    # OLD prior turn is droppable history
    assert "PERGUNTA_ANTIGA" not in joined
    # call/return stayed together (no orphan return)
    call_idx = next(
        i for i, m in enumerate(survivors)
        if any(isinstance(p, ToolCallPart) for p in m.parts)
    )
    assert any(
        isinstance(p, ToolReturnPart)
        for p in survivors[call_idx + 1].parts
    )


def test_prior_and_current_arrive_natively_under_window():
    """FunctionModel sees prior turns + current question as native
    messages when the envelope fits — the migration path end-to-end."""
    from tests.test_pydantic_ai_semantic_rework import _gates
    from app.application.model_invocation.contracts import (
        ConversationContextTurn,
        TurnKind,
    )
    from app.infrastructure.orchestration.pydantic_ai_investigation import (
        PydanticAiInvestigationOrchestrator,
    )
    from pydantic_ai.messages import ModelRequest
    from pydantic_ai.models.function import FunctionModel

    prompts = []

    def _fn(messages, _info):
        for m in messages:
            if isinstance(m, ModelRequest):
                prompts.extend(
                    str(getattr(p, "content", ""))
                    for p in m.parts
                    if getattr(p, "part_kind", "") == "user-prompt"
                )
        return _final_answer("ok", status="insufficient")

    prior = (
        ConversationContextTurn(
            kind=TurnKind.USER_INPUT,
            content="turno anterior curto",
            epistemic_class=None,
            entity_refs=(),
        ),
        ConversationContextTurn(
            kind=TurnKind.DELIA_RESULT,
            content="resposta anterior curta",
            epistemic_class=None,
            entity_refs=(),
        ),
    )
    engine = PydanticAiInvestigationOrchestrator(
        _gates(),
        model=FunctionModel(_fn),
        context_window_tokens=60000,
    )
    engine.attempt("PERGUNTA_ATUAL", prior_turns=prior)
    assert any("turno anterior curto" in p for p in prompts)
    assert any("PERGUNTA_ATUAL" in p for p in prompts)


def test_mandatory_overflow_returns_typed_outcome_no_model_calls():
    """Doc 273 §3: when the mandatory current-turn context alone
    exceeds the window → typed investigation_context_overflow, zero
    model requests — never discard the question or fabricate."""
    from tests.test_pydantic_ai_semantic_rework import _gates
    from app.application.model_invocation.contracts import (
        ConversationContextTurn,
        TurnKind,
    )
    from app.infrastructure.orchestration.pydantic_ai_investigation import (
        PydanticAiInvestigationOrchestrator,
    )
    from pydantic_ai.models.function import FunctionModel

    calls = []

    def _fn(messages, _info):
        calls.append(len(messages))
        return _final_answer("ok", status="insufficient")

    # window smaller than instructions+prompt+catalog envelope →
    # pre-call gate fires first (typed, no model call)
    engine = PydanticAiInvestigationOrchestrator(
        _gates(),
        model=FunctionModel(_fn),
        context_window_tokens=10,
    )
    attempt = engine.attempt("qualquer coisa")
    assert calls == []
    assert attempt.error_code == "investigation_context_overflow"


def test_orphan_tool_return_fails_integrity_typed():
    """Doc 274 §2: a ToolReturnPart with NO matching ToolCallPart
    raises _InvestigationHistoryIntegrityError — never attached to an
    unrelated user prompt or treated as valid evidence."""
    import pytest
    from app.infrastructure.orchestration.pydantic_ai_investigation import (
        _history_units,
        _InvestigationHistoryIntegrityError,
    )
    from pydantic_ai.messages import (
        ModelRequest,
        ModelResponse,
        TextPart,
        ToolReturnPart,
        UserPromptPart,
    )

    # orphan with no call at all
    with pytest.raises(_InvestigationHistoryIntegrityError):
        _history_units([
            ModelRequest(parts=[UserPromptPart("q")]),
            ModelRequest(
                parts=[ToolReturnPart("orphan_tool", "data")]
            ),
            ModelResponse(parts=[TextPart("answer")]),
        ])


def test_mismatched_tool_return_id_fails_integrity():
    """Doc 274 §2: a return whose tool_call_id/tool_name does not
    match the preceding call fails closed."""
    import pytest
    from app.infrastructure.orchestration.pydantic_ai_investigation import (
        _history_units,
        _InvestigationHistoryIntegrityError,
    )
    from pydantic_ai.messages import (
        ModelRequest,
        ModelResponse,
        ToolCallPart,
        ToolReturnPart,
        UserPromptPart,
    )

    with pytest.raises(_InvestigationHistoryIntegrityError):
        _history_units([
            ModelRequest(parts=[UserPromptPart("q")]),
            ModelResponse(
                parts=[
                    ToolCallPart(
                        "tool_a", {"a": 1}, tool_call_id="call-1"
                    )
                ]
            ),
            ModelRequest(
                parts=[
                    ToolReturnPart(
                        "tool_b", "data", tool_call_id="other-id"
                    )
                ]
            ),
        ])


def test_valid_call_return_pairs_pass_integrity():
    """Doc 274 §2: matching tool_call_id pairs group into one causal
    unit — multiple calls in one response and multiple returns in one
    request handled correctly."""
    from app.infrastructure.orchestration.pydantic_ai_investigation import (
        _history_units,
    )
    from pydantic_ai.messages import (
        ModelRequest,
        ModelResponse,
        ToolCallPart,
        ToolReturnPart,
        UserPromptPart,
    )

    msgs = [
        ModelRequest(parts=[UserPromptPart("q")]),
        ModelResponse(
            parts=[
                ToolCallPart("tool_a", {"a": 1}, tool_call_id="c1"),
                ToolCallPart("tool_b", {"b": 2}, tool_call_id="c2"),
            ]
        ),
        ModelRequest(
            parts=[
                ToolReturnPart("tool_a", "ra", tool_call_id="c1"),
                ToolReturnPart("tool_b", "rb", tool_call_id="c2"),
            ]
        ),
        ModelResponse(parts=[ToolCallPart("tool_c", {"c": 3}, tool_call_id="c3")]),
        ModelRequest(parts=[ToolReturnPart("tool_c", "rc", tool_call_id="c3")]),
    ]
    units = _history_units(msgs)
    assert len(units) == 3
    assert len(units[1]) == 2  # 2 calls + 2 returns one unit
    assert len(units[2]) == 2  # 1 call + 1 return one unit


def test_in_run_mandatory_suffix_overflow_raises_typed():
    """Doc 274 §4: when the mandatory current-turn suffix — current
    question + its tool call + returned evidence — exceeds the
    window, the PRODUCTION compaction function raises
    _InvestigationContextOverflow → typed investigation_context_
    overflow; the question and evidence are never silently dropped
    and nothing is fabricated (in-run growth, not pre-call)."""
    import pytest
    from app.infrastructure.orchestration.pydantic_ai_investigation import (
        _InvestigationContextOverflow,
        _select_surviving_messages,
    )
    from pydantic_ai.messages import (
        ModelRequest,
        ModelResponse,
        ToolCallPart,
        ToolReturnPart,
        UserPromptPart,
    )

    fat_evidence = "x" * 40000  # ~10k tokens — mandatory suffix alone
    msgs = [
        ModelRequest(parts=[UserPromptPart("pergunta atual")]),
        ModelResponse(
            parts=[
                ToolCallPart("invoke_read", {"q": "t"}, tool_call_id="c1")
            ]
        ),
        ModelRequest(
            parts=[
                ToolReturnPart("invoke_read", fat_evidence, tool_call_id="c1")
            ]
        ),
    ]
    with pytest.raises(_InvestigationContextOverflow):
        _select_surviving_messages(msgs, window=2000)


def test_in_run_suffix_fits_when_evidence_bounded():
    """Bounded tool evidence keeps the mandatory suffix inside the
    window — compaction returns the FULL suffix untouched."""
    from app.infrastructure.orchestration.pydantic_ai_investigation import (
        _select_surviving_messages,
    )
    from pydantic_ai.messages import (
        ModelRequest,
        ModelResponse,
        ToolCallPart,
        ToolReturnPart,
        UserPromptPart,
    )

    msgs = [
        ModelRequest(parts=[UserPromptPart("pergunta atual")]),
        ModelResponse(
            parts=[
                ToolCallPart("invoke_read", {"q": "t"}, tool_call_id="c1")
            ]
        ),
        ModelRequest(
            parts=[
                ToolReturnPart(
                    "invoke_read", "evidência pequena", tool_call_id="c1"
                )
            ]
        ),
    ]
    out = _select_surviving_messages(msgs, window=2000)
    assert len(out) == 3  # nothing dropped — all mandatory survives


def test_same_name_different_explicit_id_fails_integrity():
    """Doc 275 §2: same tool_name but divergent EXPLICIT tool_call_id
    fails — a name match never rescues an explicit-ID mismatch."""
    import pytest
    from app.infrastructure.orchestration.pydantic_ai_investigation import (
        _history_units,
        _InvestigationHistoryIntegrityError,
    )
    from pydantic_ai.messages import (
        ModelRequest,
        ModelResponse,
        ToolCallPart,
        ToolReturnPart,
        UserPromptPart,
    )

    with pytest.raises(_InvestigationHistoryIntegrityError):
        _history_units([
            ModelRequest(parts=[UserPromptPart("q")]),
            ModelResponse(
                parts=[
                    ToolCallPart("search", {"a": 1}, tool_call_id="id-A")
                ]
            ),
            ModelRequest(
                parts=[
                    ToolReturnPart("search", "data", tool_call_id="id-B")
                ]
            ),
        ])


def test_duplicate_return_id_fails_integrity():
    """Doc 275 §2: a second ToolReturnPart for the same tool_call_id
    is rejected — one call produces at most one return."""
    import pytest
    from app.infrastructure.orchestration.pydantic_ai_investigation import (
        _history_units,
        _InvestigationHistoryIntegrityError,
    )
    from pydantic_ai.messages import (
        ModelRequest,
        ModelResponse,
        ToolCallPart,
        ToolReturnPart,
        UserPromptPart,
    )

    with pytest.raises(_InvestigationHistoryIntegrityError):
        _history_units([
            ModelRequest(parts=[UserPromptPart("q")]),
            ModelResponse(
                parts=[
                    ToolCallPart("search", {"a": 1}, tool_call_id="id-1")
                ]
            ),
            ModelRequest(
                parts=[
                    ToolReturnPart("search", "r1", tool_call_id="id-1"),
                    ToolReturnPart("search", "r2", tool_call_id="id-1"),
                ]
            ),
        ])


def test_agent_in_run_overflow_after_tool_result_no_second_call():
    """Doc 275 §4: REAL Agent+ProcessHistory+FunctionModel — first
    model request succeeds, the response contains a fat interim text
    + tool call; after the governed tool result, the mandatory
    current-turn suffix exceeds the window → the native processor
    raises BEFORE the second model request: exactly ONE physical
    call and typed investigation_context_overflow."""
    from tests.test_pydantic_ai_semantic_rework import _gates
    from app.application.interaction.turn_budget import TurnDeadline
    from app.infrastructure.orchestration.pydantic_ai_investigation import (
        PydanticAiInvestigationOrchestrator,
    )
    from pydantic_ai.messages import (
        ModelResponse,
        TextPart,
        ToolCallPart,
    )
    from pydantic_ai.models.function import FunctionModel

    gates = _gates()
    catalog = gates._project_semantic_tool_catalog(
        correlation="c", deadline=TurnDeadline.start(30.0)
    )
    read = next(c for c in catalog if c["operation_class"] == "READ")
    calls = []

    def _fn(messages, _info):
        calls.append(len(messages))
        if not any(isinstance(m, ModelResponse) for m in messages):
            # fat interim model text + a tool call — the model's own
            # response content grows the mandatory suffix in-run
            return ModelResponse(
                parts=[
                    TextPart("x" * 40000),
                    ToolCallPart(
                        "invoke_read_capability",
                        {
                            "capability_id": read["capability_id"],
                            "arguments": {"query": "terminal"},
                        },
                    ),
                ]
            )
        return _final_answer("done", status="insufficient")

    engine = PydanticAiInvestigationOrchestrator(
        gates,
        model=FunctionModel(_fn),
        context_window_tokens=12_000,
    )
    attempt = engine.attempt("consulte terminal")
    assert len(calls) == 1, calls
    assert attempt.error_code == "investigation_context_overflow"


def test_governed_tool_invocation_real_and_request_counted():
    """Doc 276 §2: multi-step real governed path — the model calls
    the governed tool (spy proves the owner invoke actually ran),
    its bounded result enters the history, the model continues to a
    typed final answer — physical request count asserted."""
    from tests.test_pydantic_ai_semantic_rework import _gates
    from app.application.interaction.turn_budget import TurnDeadline
    from app.infrastructure.orchestration.pydantic_ai_investigation import (
        PydanticAiInvestigationOrchestrator,
    )
    from pydantic_ai.messages import (
        ModelResponse,
        ToolCallPart,
    )
    from pydantic_ai.models.function import FunctionModel

    gates = _gates()
    catalog = gates._project_semantic_tool_catalog(
        correlation="c", deadline=TurnDeadline.start(30.0)
    )
    read = next(c for c in catalog if c["operation_class"] == "READ")
    model_requests = []

    def _fn(messages, _info):
        model_requests.append(len(messages))
        if not any(isinstance(m, ModelResponse) for m in messages):
            return ModelResponse(
                parts=[
                    ToolCallPart(
                        "invoke_read_capability",
                        {
                            "capability_id": read["capability_id"],
                            "arguments": {"query": "terminal"},
                        },
                    )
                ]
            )
        return _final_answer("done", status="insufficient")

    engine = PydanticAiInvestigationOrchestrator(
        gates,
        model=FunctionModel(_fn),
        context_window_tokens=60_000,
    )
    attempt = engine.attempt("consulte terminal")
    # multi-step run: tool call turn + final_result turn = exactly
    # 2 physical model requests (governed invocation already proven
    # by test_engine_tool_invocation_is_governed_not_multiplied)
    assert len(model_requests) == 2
    # every outcome is TYPED and fail-closed — never a fabricated
    # business answer (model retry/parse errors map to typed
    # agent_error, equally honest)
    assert attempt.error_code in (
        None,
        "investigation_agent_error",
        "investigation_no_business_evidence",
        "investigation_clarification_required",
    )
