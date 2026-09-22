"""UnderstandStructuredInput — C3-T4 bounded vertical slice.

BOUNDED_SOURCE_OBSERVATION_EXTRACTION on top of InvokeModel.
Not chat, planner, RAG, tool execution, or ACT.
"""

from __future__ import annotations

from app.application.model_invocation.contracts import ModelInvocationRequest
from app.application.model_invocation.errors import ModelInvocationError
from app.application.model_invocation.invoke_model import InvokeModel
from app.application.structured_understanding.contracts import (
    StructuredUnderstandingRequest,
    StructuredUnderstandingResult,
)
from app.application.structured_understanding.errors import (
    EPISTEMIC_VIOLATION,
    FORBIDDEN_RESULT_FIELD,
    INVALID_REQUEST,
    INVALID_STRUCTURED_RESULT,
    UNSUPPORTED_SCHEMA,
    StructuredUnderstandingError,
)
from app.domain.evidence.model import EpistemicClass
from app.domain.structured_understanding.rules import (
    SCHEMA_SOURCE_OBSERVATION_V1,
    SCHEMA_VERSION_V1,
    StructuredUnderstandingDomainError,
    build_content_from_structured_output,
    confidence_does_not_establish_fact,
    reject_world_fact_promotion,
)


EXPECTED_FIELDS = ("observations",)
MAX_SOURCE_CHARS = 16_384


class UnderstandStructuredInput:
    def __init__(self, invoke_model: InvokeModel) -> None:
        self._invoke_model = invoke_model

    def execute(
        self, request: StructuredUnderstandingRequest
    ) -> StructuredUnderstandingResult:
        self._validate_request(request)
        if request.declared_result_epistemic_class is EpistemicClass.FACT:
            raise StructuredUnderstandingError(
                EPISTEMIC_VIOLATION,
                "declared structured understanding FACT is forbidden",
            )

        invocation_request = ModelInvocationRequest(
            invocation_id=request.invocation_id,
            model_ref=request.model_ref,
            input_text=request.source_text,
            task_purpose_id=request.task_purpose_id,
            output_schema_id=request.output_schema_id,
            output_schema_version=request.output_schema_version,
            expected_fields=EXPECTED_FIELDS,
            instruction_lineage=request.instruction_lineage,
            timeout_seconds=request.timeout_seconds,
            evidence_refs=request.evidence_refs,
            source_refs=request.source_refs,
            declared_epistemic_class=EpistemicClass.OBSERVATION,
            authority_policy=request.authority_policy,
            untrusted_external_metadata=request.untrusted_external_metadata,
            eval_bind=request.eval_bind,
        )
        try:
            model_result = self._invoke_model.execute(invocation_request)
        except ModelInvocationError as exc:
            raise StructuredUnderstandingError(exc.code, exc.message) from exc

        try:
            content = build_content_from_structured_output(
                model_result.structured_output,
                evidence_refs=request.evidence_refs,
                source_refs=request.source_refs,
            )
        except StructuredUnderstandingDomainError as exc:
            message = str(exc)
            code = INVALID_STRUCTURED_RESULT
            lowered = message.lower()
            if "fact" in lowered:
                code = EPISTEMIC_VIOLATION
            elif "forbidden field" in lowered or "secret" in lowered or "chain_of_thought" in lowered:
                code = FORBIDDEN_RESULT_FIELD
            elif "unsupported" in lowered and "schema" in lowered:
                code = UNSUPPORTED_SCHEMA
            raise StructuredUnderstandingError(code, message) from exc

        result_class = EpistemicClass.OBSERVATION
        if not content.observations:
            # No observation produced — result remains non-FACT; class stays OBSERVATION
            # with explicit limitations (missing != false / != world absence).
            result_class = EpistemicClass.OBSERVATION
        try:
            reject_world_fact_promotion(result_class)
        except StructuredUnderstandingDomainError as exc:
            raise StructuredUnderstandingError(EPISTEMIC_VIOLATION, str(exc)) from exc

        _ = confidence_does_not_establish_fact(None)

        return StructuredUnderstandingResult(
            understanding_id=request.understanding_id,
            schema_id=request.output_schema_id,
            schema_version=request.output_schema_version,
            content=content,
            epistemic_class=result_class,
            evidence_refs=request.evidence_refs,
            source_refs=request.source_refs,
            model_ref=request.model_ref,
            lineage=model_result.lineage,
            generated_at=model_result.generated_at,
            confidence=None,
        )

    def _validate_request(self, request: StructuredUnderstandingRequest) -> None:
        if request.output_schema_id != SCHEMA_SOURCE_OBSERVATION_V1:
            raise StructuredUnderstandingError(
                UNSUPPORTED_SCHEMA,
                f"unsupported schema_id '{request.output_schema_id}'",
            )
        if request.output_schema_version != SCHEMA_VERSION_V1:
            raise StructuredUnderstandingError(
                UNSUPPORTED_SCHEMA,
                f"unsupported schema_version '{request.output_schema_version}'",
            )
        if not request.task_purpose_id.strip():
            raise StructuredUnderstandingError(INVALID_REQUEST, "task_purpose_id is required")
        if not request.source_text.strip():
            raise StructuredUnderstandingError(INVALID_REQUEST, "source_text is required")
        if len(request.source_text) > MAX_SOURCE_CHARS:
            raise StructuredUnderstandingError(INVALID_REQUEST, "source_text exceeds bound")
        if request.timeout_seconds <= 0 or request.timeout_seconds > 30.0:
            raise StructuredUnderstandingError(
                INVALID_REQUEST,
                "timeout_seconds must be in (0, 30]",
            )
