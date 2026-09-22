"""C3-T4 Structured Understanding foundation tests.

Deterministic TEST_ONLY adapter. Not real-model quality evidence.
"""

from __future__ import annotations

from dataclasses import fields

import pytest

from app.application.model_invocation.contracts import EvalBindRequest
from app.application.model_invocation.invoke_model import InvokeModel
from app.application.structured_understanding.contracts import (
    StructuredUnderstandingRequest,
)
from app.application.structured_understanding.errors import (
    EPISTEMIC_VIOLATION,
    FORBIDDEN_RESULT_FIELD,
    INVALID_STRUCTURED_RESULT,
    UNSUPPORTED_SCHEMA,
    StructuredUnderstandingError,
)
from app.application.structured_understanding.understand_structured_input import (
    UnderstandStructuredInput,
)
from app.domain.evidence.model import (
    EpistemicClass,
    EvidenceRef,
    ModelRef,
    SourceRef,
)
from app.domain.model_invocation.model import (
    InstructionLineage,
    ModelInvocationId,
)
from app.domain.structured_understanding.model import StructuredUnderstandingId
from app.domain.structured_understanding.rules import (
    SCHEMA_SOURCE_OBSERVATION_V1,
    SCHEMA_VERSION_V1,
    confidence_does_not_establish_fact,
)
from app.infrastructure.model_invocation.deterministic_test_adapter import (
    DeterministicTestAdapter,
)


def _model() -> ModelRef:
    return ModelRef(model_id="delia-test-model", version="0.0-test", owner_ref="delia")


def _request(**overrides) -> StructuredUnderstandingRequest:
    values = dict(
        understanding_id=StructuredUnderstandingId("su-1"),
        invocation_id=ModelInvocationId("inv-su-1"),
        model_ref=_model(),
        source_text='TEST FIXTURE: "Machine X stopped at 14:32"',
        task_purpose_id="c3t4.source_observation",
        output_schema_id=SCHEMA_SOURCE_OBSERVATION_V1,
        output_schema_version=SCHEMA_VERSION_V1,
        instruction_lineage=InstructionLineage(
            instruction_id="c3t4.observation",
            version="1",
            content_hash="sha256:fixture",
        ),
        timeout_seconds=5.0,
        evidence_refs=(EvidenceRef("ev-su-1"),),
        source_refs=(SourceRef(source_id="src-su-1", source_system="fixture"),),
        eval_bind=EvalBindRequest(
            eval_id="c3t4.foundation.positive",
            target_sha="target-sha-su",
            fixture_id="fixture-su-positive",
        ),
    )
    values.update(overrides)
    return StructuredUnderstandingRequest(**values)


def _execute(behavior: str = "success", request: StructuredUnderstandingRequest | None = None):
    use_case = UnderstandStructuredInput(InvokeModel(DeterministicTestAdapter(behavior=behavior)))
    return use_case.execute(request or _request())


def test_positive_source_observation_extraction():
    result = _execute()
    assert result.epistemic_class is EpistemicClass.OBSERVATION
    assert result.is_fact() is False
    assert result.is_world_fact() is False
    assert len(result.content.observations) == 1
    obs = result.content.observations[0]
    assert obs.epistemic_class is EpistemicClass.OBSERVATION
    assert obs.is_world_fact() is False
    assert "source states" in obs.content
    assert result.evidence_refs == (EvidenceRef("ev-su-1"),)
    assert result.source_refs[0].source_id == "src-su-1"
    assert result.model_ref == _model()
    assert result.lineage.model_ref == _model()
    assert result.lineage.instruction_lineage.instruction_id == "c3t4.observation"
    assert result.lineage.configuration_lineage.output_schema_id == SCHEMA_SOURCE_OBSERVATION_V1


def test_source_observation_is_not_world_fact():
    result = _execute()
    obs = result.content.observations[0]
    assert obs.epistemic_class is EpistemicClass.OBSERVATION
    assert obs.is_world_fact() is False
    assert result.is_world_fact() is False
    # Source statement extraction must not be treated as verified world event.
    assert "Machine X stopped" in obs.content or "source states" in obs.content


def test_observation_item_claiming_fact_is_rejected():
    with pytest.raises(StructuredUnderstandingError) as exc:
        _execute("su_claim_fact")
    assert exc.value.code == EPISTEMIC_VIOLATION


def test_result_level_fact_claim_is_rejected():
    with pytest.raises(StructuredUnderstandingError) as exc:
        _execute("su_result_claim_fact")
    assert exc.value.code == EPISTEMIC_VIOLATION


def test_declared_fact_request_is_rejected():
    with pytest.raises(StructuredUnderstandingError) as exc:
        _execute(request=_request(declared_result_epistemic_class=EpistemicClass.FACT))
    assert exc.value.code == EPISTEMIC_VIOLATION


def test_evidence_and_source_refs_preserved():
    result = _execute()
    assert result.evidence_refs[0].evidence_id == "ev-su-1"
    assert result.lineage.evidence_refs[0].evidence_id == "ev-su-1"
    assert result.lineage.source_refs[0].source_system == "fixture"


def test_eval_identity_bound_but_no_eval_result():
    result = _execute()
    assert result.lineage.eval_identity is not None
    assert result.lineage.eval_identity.target_sha == "target-sha-su"
    assert result.has_eval_result() is False
    assert "eval_result" not in {f.name for f in fields(result)}


def test_conflicting_observations_preserved():
    result = _execute("su_conflict")
    assert result.content.conflict_present is True
    assert len(result.content.observations) == 2
    assert any(note.code == "conflicting_evidence" for note in result.content.limitations)
    assert result.is_fact() is False


def test_missing_evidence_is_not_false():
    result = _execute("su_missing")
    assert result.content.observations == ()
    assert any(note.code == "insufficient_evidence" for note in result.content.limitations)
    assert result.is_world_fact() is False
    assert result.is_fact() is False


def test_invalid_schema_rejected():
    with pytest.raises(StructuredUnderstandingError) as exc:
        _execute("su_invalid_schema")
    assert exc.value.code in {INVALID_STRUCTURED_RESULT, "invalid_structured_output"}


def test_unsupported_schema_id_rejected():
    with pytest.raises(StructuredUnderstandingError) as exc:
        _execute(request=_request(output_schema_id="c3t4.unknown"))
    assert exc.value.code == UNSUPPORTED_SCHEMA


def test_secret_bearing_output_rejected():
    with pytest.raises(StructuredUnderstandingError) as exc:
        _execute("secret")
    assert exc.value.code in {FORBIDDEN_RESULT_FIELD, "invalid_structured_output"}


def test_cot_bearing_output_rejected():
    with pytest.raises(StructuredUnderstandingError) as exc:
        _execute("cot")
    assert exc.value.code in {FORBIDDEN_RESULT_FIELD, "invalid_structured_output"}


def test_tool_calls_do_not_execute():
    with pytest.raises(StructuredUnderstandingError) as exc:
        _execute("tool_calls")
    assert exc.value.code in {FORBIDDEN_RESULT_FIELD, "invalid_structured_output"}


def test_recommendation_does_not_authorize_act():
    result = _execute()
    assert result.authorizes_act() is False


def test_confidence_does_not_establish_fact():
    assert confidence_does_not_establish_fact(0.99) is True
    result = _execute()
    assert result.confidence is None
    assert result.is_fact() is False


def test_lineage_does_not_grant_authorization():
    result = _execute()
    assert result.lineage.grants_authorization() is False
    assert result.lineage.grants_act() is False
