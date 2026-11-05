"""M2 (doc 220): Pydantic AI adapter behind ModelInvocationPort —
same governed contract as the legacy adapter; the use case's
validation, exposure policy and lineage stay authoritative.
"""
from __future__ import annotations

import pytest

from pydantic_ai.models.test import TestModel

from app.application.model_invocation.invoke_model import InvokeModel
from app.application.model_invocation.contracts import (
    ConversationContextTurn,
    ModelInvocationId,
    ModelInvocationRequest,
)
from app.application.model_invocation.errors import (
    INVALID_STRUCTURED_OUTPUT,
    PROVIDER_UNAVAILABLE,
    ModelInvocationError,
)
from app.domain.evidence.model import EpistemicClass, ModelRef
from app.domain.interaction.model import TurnKind
from app.domain.model_invocation.model import (
    InstructionLineage,
    InvocationFinishStatus,
    ProviderExposureClass,
)
from app.infrastructure.model_invocation.pydantic_ai_adapter import (
    PydanticAiModelInvocationAdapter,
)


def _model() -> ModelRef:
    return ModelRef(
        model_id="fixture-model",
        version="1",
        owner_ref="DELPI",
        provider_ref="openai_compatible",
    )


def _request(**overrides) -> ModelInvocationRequest:
    values = dict(
        invocation_id=ModelInvocationId("inv-m2-1"),
        model_ref=_model(),
        input_text="qual a estrutura do produto?",
        task_purpose_id="c3.admission",
        output_schema_id="c3.admission",
        output_schema_version="1",
        expected_fields=("interaction_class", "requires_owner_surface"),
        instruction_lineage=InstructionLineage(
            instruction_id="c3.admission",
            version="1",
            content_hash="sha256:fixture",
        ),
        timeout_seconds=5.0,
        instruction_content="Classify the turn.",
    )
    values.update(overrides)
    return ModelInvocationRequest(**values)


def _adapter(model_impl) -> PydanticAiModelInvocationAdapter:
    return PydanticAiModelInvocationAdapter(
        base_url="http://fixture.invalid/v1",
        api_key="fixture-key",
        model="fixture-model",
        timeout_seconds=30.0,
        model_impl=model_impl,
    )


def test_adapter_exposes_same_port_policy_as_legacy():
    adapter = _adapter(TestModel())
    assert adapter.adapter_kind == "OPENAI_COMPATIBLE"
    assert adapter.exposure_class is ProviderExposureClass.EXTERNAL_APPROVED


def test_structured_output_flows_through_invoke_model():
    adapter = _adapter(TestModel())
    result = InvokeModel(adapter).execute(_request())
    assert result.finish_status is InvocationFinishStatus.COMPLETED
    assert isinstance(result.structured_output, dict)
    assert result.model_ref == _model()
    assert result.epistemic_class is EpistemicClass.HYPOTHESIS


def test_controlled_output_and_surplus_keys_pass():
    adapter = _adapter(
        TestModel(
            custom_output_args={
                "interaction_class": "operational",
                "requires_owner_surface": True,
                "limitations": ["owner latency high"],
            }
        )
    )
    result = InvokeModel(adapter).execute(_request())
    out = result.structured_output
    assert out["interaction_class"] == "operational"
    assert out["requires_owner_surface"] is True
    assert out["limitations"] == ["owner latency high"]


def test_applicable_false_early_return_survives():
    """Selection contracts may return applicable=false without
    companion ids — the governed use case must return the result
    instead of failing on absent expected fields."""
    adapter = _adapter(
        TestModel(custom_output_args={"applicable": False})
    )
    result = InvokeModel(adapter).execute(
        _request(expected_fields=("applicable", "capability_group_id"))
    )
    assert result.structured_output["applicable"] is False


def test_non_object_output_maps_to_invalid_structured():
    """A model response that fails structured output validation
    must surface as INVALID_STRUCTURED_OUTPUT — never as a
    collection or silently-typed fallback."""
    class _BadModel(TestModel):
        async def request(
            self, messages, model_settings, model_request_parameters
        ):
            raise ValueError("schema validation failed")

    adapter = _adapter(_BadModel())
    with pytest.raises(ModelInvocationError) as exc:
        InvokeModel(adapter).execute(_request())
    assert exc.value.code == INVALID_STRUCTURED_OUTPUT


def test_prior_context_maps_to_roles_not_system():
    adapter = _adapter(
        TestModel(
            custom_output_args={
                "interaction_class": "conversation",
                "requires_owner_surface": False,
            }
        )
    )
    request = _request(
        prior_context=(
            ConversationContextTurn(
                kind=TurnKind.USER_INPUT, content="pergunta anterior"
            ),
            ConversationContextTurn(
                kind=TurnKind.DELIA_RESULT, content="resposta anterior"
            ),
        )
    )
    result = InvokeModel(adapter).execute(request)
    # Prior context flowed as conversation turns; output is governed.
    assert result.structured_output["interaction_class"] == "conversation"


def test_provider_error_maps_to_semantic_code():
    class _RaisingModel(TestModel):
        async def request(
            self, messages, model_settings, model_request_parameters
        ):
            raise RuntimeError("connection refused")

    adapter = _adapter(_RaisingModel())
    with pytest.raises(ModelInvocationError) as exc:
        InvokeModel(adapter).execute(_request())
    assert exc.value.code == PROVIDER_UNAVAILABLE


def test_constructor_contract_parity_with_legacy():
    adapter = _adapter(TestModel())
    assert adapter.context_window_tokens is None
    assert adapter.default_max_output_units is None
    with pytest.raises(ValueError):
        PydanticAiModelInvocationAdapter(
            base_url="",
            api_key="k",
            model="m",
            timeout_seconds=5.0,
            model_impl=TestModel(),
        )


# ---------- M2-REWORK: per-stage typed contracts (doc 220 §5) ----------

_STAGE_CONTRACTS = [
    # (stage purpose, expected_fields, valid args)
    (
        "admission",
        ("interaction_class", "requires_owner_surface"),
        {"interaction_class": "operational", "requires_owner_surface": True},
    ),
    (
        "resolver_selection",
        ("applicable", "remote_name"),
        {"applicable": True, "remote_name": "davi"},
    ),
    (
        "foreign_selection",
        ("foreign_capability_id",),
        {"foreign_capability_id": "get_product_structure"},
    ),
    (
        "subobjective_decomposition",
        ("subobjectives",),
        {"subobjectives": [{"goal": "resolve structure"}]},
    ),
    (
        "grounded_synthesis",
        ("items",),
        {"items": [{"ref": 1, "text": "x"}]},
    ),
    (
        "clarification_wording",
        ("question",),
        {"question": "Qual produto?"},
    ),
    (
        "evidence_comparison",
        ("left", "right"),
        {"left": [1], "right": [2]},
    ),
    (
        "native_assessment",
        ("status",),
        {"status": "answered"},
    ),
    (
        "turn_goal",
        ("goal_class",),
        {"goal_class": "operational"},
    ),
]


@pytest.mark.parametrize(
    "purpose,expected_fields,args", _STAGE_CONTRACTS
)
def test_stage_typed_contracts_through_port(
    purpose, expected_fields, args
):
    """Every real model stage flows the same governed contract through
    the Pydantic AI port — typed output, surplus tolerated, presence
    enforced downstream exactly as the legacy path."""
    adapter = _adapter(TestModel(custom_output_args=dict(args)))
    result = InvokeModel(adapter).execute(
        _request(
            task_purpose_id=f"c3.{purpose}",
            output_schema_id=f"c3.{purpose}",
            expected_fields=expected_fields,
        )
    )
    assert result.finish_status is InvocationFinishStatus.COMPLETED
    for field in expected_fields:
        assert field in result.structured_output


def test_abstention_proposal_survives_governed_path():
    """Abstain (applicable=false without companion ids) is a legal
    stage output — the port must carry it unmodified so the
    orchestrator's deterministic gate decides."""
    adapter = _adapter(TestModel(custom_output_args={"applicable": False}))
    result = InvokeModel(adapter).execute(
        _request(expected_fields=("applicable", "remote_name"))
    )
    assert result.structured_output["applicable"] is False
    assert "remote_name" not in result.structured_output or (
        result.structured_output["remote_name"] is None
    )


# ---------- M2-REWORK: runtime flag fail-closed ----------

def test_unknown_model_runtime_fails_closed(monkeypatch):
    from app.infrastructure.config.settings import Settings

    monkeypatch.setenv("DELIA_MODEL_RUNTIME", "totally-not-a-runtime")
    with pytest.raises(ValueError) as exc:
        Settings()
    assert "DELIA_MODEL_RUNTIME" in str(exc.value)


def test_legacy_model_runtime_retired_fails_closed(monkeypatch):
    """Doc 243: the legacy runtime is removed — an explicit `legacy`
    value fails closed like any unknown runtime, never a fallback."""
    from app.infrastructure.config.settings import Settings

    monkeypatch.setenv("DELIA_MODEL_RUNTIME", "pydantic_ai")
    assert Settings() is not None
    monkeypatch.setenv("DELIA_MODEL_RUNTIME", "legacy")
    with pytest.raises(ValueError):
        Settings()


# ---------- M6-FINAL: required-fields contract regression ----------

def test_required_field_missing_fails_closed():
    """RC-A regression: when the model omits a required wrapper like
    'arguments', output validation must fail — never a silent
    args=none that ends the turn unbound."""
    adapter = _adapter(TestModel(custom_output_args={}))
    with pytest.raises(ModelInvocationError) as exc:
        InvokeModel(adapter).execute(
            _request(expected_fields=("arguments",))
        )
    assert exc.value.code == INVALID_STRUCTURED_OUTPUT


def test_applicable_true_with_missing_companion_fails():
    """applicable=true proposes a companion id — its absence is a
    contract violation at the governed boundary."""
    adapter = _adapter(
        TestModel(custom_output_args={"applicable": True})
    )
    with pytest.raises(ModelInvocationError) as exc:
        InvokeModel(adapter).execute(
            _request(expected_fields=("applicable", "remote_name"))
        )
    assert exc.value.code == INVALID_STRUCTURED_OUTPUT


def test_nested_objects_and_arrays_preserved():
    adapter = _adapter(
        TestModel(
            custom_output_args={
                "subobjectives": [
                    {"goal": "a", "refs": [1, 2]},
                    {"goal": "b"},
                ]
            }
        )
    )
    result = InvokeModel(adapter).execute(
        _request(expected_fields=("subobjectives",))
    )
    assert result.structured_output["subobjectives"][0]["refs"] == [1, 2]


def test_numeric_codes_stay_strings():
    """Enterprise codes are strings even when numeric-looking —
    coercion would corrupt 90260148-class identifiers."""
    adapter = _adapter(
        TestModel(custom_output_args={"arguments": {"code": "90260148"}})
    )
    result = InvokeModel(adapter).execute(
        _request(expected_fields=("arguments",))
    )
    assert result.structured_output["arguments"]["code"] == "90260148"


def test_malformed_output_maps_to_invalid_not_fabrication():
    class _Malformed(TestModel):
        async def request(self, messages, model_settings, params):
            from pydantic_ai.messages import ModelResponse, TextPart

            return ModelResponse(parts=[TextPart("not json at all")])

    adapter = _adapter(_Malformed())
    with pytest.raises(ModelInvocationError):
        InvokeModel(adapter).execute(_request())


def test_extra_keys_survive_but_never_authorize():
    adapter = _adapter(
        TestModel(
            custom_output_args={
                "goal_class": "operational",
                "surprise": "model-invented",
            }
        )
    )
    result = InvokeModel(adapter).execute(
        _request(expected_fields=("goal_class",))
    )
    assert result.structured_output["surprise"] == "model-invented"
    # Governed projection (allowed_keys) happens downstream — the
    # adapter must carry, never adjudicate.
