"""Context Intelligence WP-A — pre-call context budget tests.

Provider-neutral policy over ModelInvocationRequest: only untrusted
prior history is reducible (oldest pairs first, alternation preserved);
mandatory content that cannot fit the declared effective window fails
closed with CONTEXT_TOO_LARGE before any provider dispatch.
"""

from __future__ import annotations

import pytest

from app.application.interaction.turn_observability import (
    ModelCallLedger,
    bind_turn_call_ledger,
    reset_turn_call_ledger,
)
from app.application.model_invocation.context_budget import (
    apply_context_budget,
)
from app.application.model_invocation.contracts import (
    ConversationContextTurn,
    ModelInvocationRequest,
)
from app.application.model_invocation.errors import (
    CONTEXT_TOO_LARGE,
    ModelInvocationError,
)
from app.application.model_invocation.invoke_model import InvokeModel
from app.domain.evidence.model import (
    EvidenceRef,
    ModelRef,
    SourceRef,
)
from app.domain.interaction.model import TurnKind
from app.domain.model_invocation.model import (
    GenerationConfig,
    InstructionLineage,
    ModelInvocationId,
)
from app.infrastructure.model_invocation.deterministic_test_adapter import (
    DeterministicTestAdapter,
)


def _model() -> ModelRef:
    return ModelRef(model_id="delia-test", version="0.1", owner_ref="delia")


def _turn(kind: TurnKind, content: str) -> ConversationContextTurn:
    return ConversationContextTurn(kind=kind, content=content)


def _history(pairs: int, chars: int) -> tuple[ConversationContextTurn, ...]:
    turns: list[ConversationContextTurn] = []
    for index in range(pairs):
        marker = f"h{index}-"
        turns.append(_turn(TurnKind.USER_INPUT, marker + "u" * (chars - len(marker))))
        turns.append(_turn(TurnKind.DELIA_RESULT, marker + "d" * (chars - len(marker))))
    return tuple(turns)


def _request(**overrides) -> ModelInvocationRequest:
    values = dict(
        invocation_id=ModelInvocationId("inv-ctx-1"),
        model_ref=_model(),
        input_text="current bounded input",
        task_purpose_id="ctx.budget",
        output_schema_id="ctx.answer",
        output_schema_version="1",
        expected_fields=("answer",),
        instruction_lineage=InstructionLineage(
            instruction_id="ctx.instruction",
            version="1",
            content_hash="sha256:fixture",
        ),
        timeout_seconds=5.0,
        evidence_refs=(EvidenceRef("ev-1"),),
        source_refs=(SourceRef(source_id="src-1", source_system="fixture"),),
    )
    values.update(overrides)
    return ModelInvocationRequest(**values)


def test_within_budget_request_is_unchanged():
    request = _request(prior_context=_history(pairs=2, chars=40))
    adjusted, observation = apply_context_budget(
        request,
        context_window_tokens=4096,
        generation_reserve_tokens=256,
    )
    assert adjusted is request
    assert observation.budget_status == "within_budget"
    assert observation.prior_turns_included == 4
    assert observation.prior_turns_omitted == 0
    assert observation.reduction_reason is None
    assert observation.estimated_input_tokens > 0
    assert observation.input_chars > 0
    assert observation.context_window_tokens == 4096


def test_over_budget_drops_oldest_pairs_preserving_alternation():
    request = _request(
        generation_config=GenerationConfig(max_output_units=200),
        prior_context=_history(pairs=6, chars=200),
    )
    adjusted, observation = apply_context_budget(
        request,
        context_window_tokens=700,
        generation_reserve_tokens=200,
    )
    assert observation.budget_status == "reduced"
    assert observation.reduction_reason == "prior_turns_omitted_for_window"
    assert observation.prior_turns_omitted > 0
    remaining = adjusted.prior_context
    assert observation.prior_turns_included == len(remaining)
    assert remaining
    assert remaining[0].kind is TurnKind.USER_INPUT
    for index, turn in enumerate(remaining):
        expected = TurnKind.USER_INPUT if index % 2 == 0 else TurnKind.DELIA_RESULT
        assert turn.kind is expected
    dropped_prefix = len(request.prior_context) - len(remaining)
    assert request.prior_context[dropped_prefix:] == remaining
    assert adjusted.input_text == request.input_text


def test_mandatory_content_alone_over_window_rejects():
    request = _request(
        input_text="x" * 6000,
        instruction_content="i" * 2000,
        prior_context=_history(pairs=2, chars=400),
    )
    adjusted, observation = apply_context_budget(
        request,
        context_window_tokens=1024,
        generation_reserve_tokens=256,
    )
    assert observation.budget_status == "rejected"
    assert adjusted.prior_context == ()
    assert observation.prior_turns_omitted == 4
    assert observation.prior_turns_included == 0


def test_empty_history_over_window_rejects_without_dispatch():
    class _Spy(DeterministicTestAdapter):
        def __init__(self):
            super().__init__(behavior="success")
            self.calls = 0

        @property
        def context_window_tokens(self):
            return 512

        def invoke(self, request):
            self.calls += 1
            return super().invoke(request)

    spy = _Spy()
    request = _request(input_text="x" * 6000, instruction_content="i" * 3000)
    with pytest.raises(ModelInvocationError) as exc:
        InvokeModel(spy).execute(request)
    assert exc.value.code == CONTEXT_TOO_LARGE
    assert exc.value.context_budget is not None
    assert exc.value.context_budget.budget_status == "rejected"
    assert spy.calls == 0


def test_reduced_history_dispatch_succeeds_and_reports_observation():
    adapter = DeterministicTestAdapter(
        behavior="success", context_window_tokens=700
    )
    request = _request(
        input_text="current bounded input",
        instruction_content="bounded instruction",
        generation_config=GenerationConfig(max_output_units=200),
        prior_context=_history(pairs=4, chars=900),
    )
    result = InvokeModel(adapter).execute(request)
    assert result.context_budget is not None
    assert result.context_budget.budget_status == "reduced"
    assert result.context_budget.prior_turns_omitted > 0


def test_unknown_window_disables_enforcement():
    adapter = DeterministicTestAdapter(behavior="success")
    assert adapter.context_window_tokens is None
    request = _request(
        input_text="x" * 4000,
        prior_context=_history(pairs=3, chars=1200),
    )
    result = InvokeModel(adapter).execute(request)
    assert result.context_budget is None
    assert result.structured_output


def test_ledger_projection_carries_context_observation():
    ledger = ModelCallLedger()
    token = bind_turn_call_ledger(ledger)
    try:
        adapter = DeterministicTestAdapter(
            behavior="success", context_window_tokens=700
        )
        request = _request(
            instruction_content="bounded instruction",
            generation_config=GenerationConfig(max_output_units=200),
            prior_context=_history(pairs=4, chars=900),
        )
        result = InvokeModel(adapter).execute(request)
        ledger.record_result(stage="ctx.stage", result=result)
        ledger.record_error(
            stage="ctx.reject",
            finish_status="error",
            error_code=CONTEXT_TOO_LARGE,
        )
    finally:
        reset_turn_call_ledger(token)
    projections = [call.to_projection() for call in ledger.calls]
    success, reject = projections
    assert success["estimated_input_tokens"] is not None
    assert success["context_window_tokens"] == 700
    assert success["prior_turns_omitted"] > 0
    assert success["context_budget_status"] == "reduced"
    assert success["input_chars"] is not None
    assert reject["error_code"] == CONTEXT_TOO_LARGE


def test_odd_first_turn_drops_singly_until_pair_boundary():
    request = _request(
        generation_config=GenerationConfig(max_output_units=200),
        prior_context=(
            _turn(TurnKind.DELIA_RESULT, "orphan " + "x" * 400),
            _turn(TurnKind.USER_INPUT, "pair-u " + "x" * 400),
            _turn(TurnKind.DELIA_RESULT, "pair-d " + "x" * 400),
        ),
    )
    adjusted, observation = apply_context_budget(
        request,
        context_window_tokens=700,
        generation_reserve_tokens=200,
    )
    remaining = adjusted.prior_context
    assert observation.prior_turns_omitted >= 1
    for index, turn in enumerate(remaining):
        expected = TurnKind.USER_INPUT if index % 2 == 0 else TurnKind.DELIA_RESULT
        assert turn.kind is expected


def test_repeated_reduction_is_idempotent_across_attempts():
    request = _request(
        instruction_content="bounded instruction",
        generation_config=GenerationConfig(max_output_units=200),
        prior_context=_history(pairs=4, chars=900),
    )
    first, obs_first = apply_context_budget(
        request, context_window_tokens=700, generation_reserve_tokens=200
    )
    second, obs_second = apply_context_budget(
        first, context_window_tokens=700, generation_reserve_tokens=200
    )
    assert obs_first.budget_status == "reduced"
    assert obs_second.budget_status == "within_budget"
    assert obs_second.prior_turns_omitted == 0
    assert second.prior_context == first.prior_context
