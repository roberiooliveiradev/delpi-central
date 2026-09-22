"""InvokeModel — bounded C3-T3 application use case.

Validates request, enforces TEST_ONLY exposure, calls ModelInvocationPort,
validates structured output, builds lineage/eval metadata.
Not a conversation, planner, RAG, or ACT runtime.
"""

from __future__ import annotations

import hashlib
from typing import Any, Mapping

from app.application.model_invocation.contracts import (
    ModelInvocationRequest,
    ModelInvocationResult,
)
from app.application.model_invocation.errors import (
    INVALID_REQUEST,
    INVALID_STRUCTURED_OUTPUT,
    POLICY_EXPOSURE_DENIED,
    PROVIDER_UNAVAILABLE,
    ModelInvocationError,
)
from app.application.ports.model_invocation_port import ModelInvocationPort
from app.domain.evidence.model import ModelRef
from app.domain.model_invocation.model import (
    ConfigurationLineage,
    EvalIdentity,
    EvalOutcome,
    EvalResult,
    ModelInvocationLineage,
    ProviderExposureClass,
)
from app.domain.model_invocation.rules import (
    ModelInvocationDomainError,
    absorb_untrusted_into_authority,
    guard_invocation_payload,
    recommendation_never_authorizes_act,
    require_model_ref_identity,
    resolve_output_epistemic_class,
)


MAX_TIMEOUT_SECONDS = 30.0
MAX_INPUT_CHARS = 16_384


class InvokeModel:
    def __init__(self, port: ModelInvocationPort) -> None:
        self._port = port

    def execute(self, request: ModelInvocationRequest) -> ModelInvocationResult:
        self._validate_request(request)
        self._enforce_exposure_policy()
        absorb_untrusted_into_authority(
            request.authority_policy,
            dict(request.untrusted_external_metadata),
        )
        try:
            payload = self._port.invoke(request)
        except ModelInvocationError:
            raise
        except Exception:
            raise ModelInvocationError(
                PROVIDER_UNAVAILABLE,
                "provider invocation failed",
            ) from None

        self._validate_structured_output(request, payload.structured_output)
        try:
            epistemic_class = resolve_output_epistemic_class(
                request.declared_epistemic_class,
                structured_output=payload.structured_output,
            )
        except ModelInvocationDomainError as exc:
            raise ModelInvocationError(INVALID_REQUEST, str(exc)) from exc

        configuration_lineage = ConfigurationLineage(
            model_ref=request.model_ref,
            instruction_lineage=request.instruction_lineage,
            output_schema_id=request.output_schema_id,
            output_schema_version=request.output_schema_version,
            generation_config=request.generation_config,
            timeout_seconds=request.timeout_seconds,
        )
        eval_result = self._bind_eval(request, configuration_lineage)
        lineage = ModelInvocationLineage(
            invocation_id=request.invocation_id,
            model_ref=request.model_ref,
            evidence_refs=request.evidence_refs,
            source_refs=request.source_refs,
            instruction_lineage=request.instruction_lineage,
            configuration_lineage=configuration_lineage,
            generated_at=payload.generated_at,
            eval_identity=eval_result.identity if eval_result else None,
        )
        return ModelInvocationResult(
            invocation_id=request.invocation_id,
            model_ref=request.model_ref,
            structured_output=dict(payload.structured_output),
            generated_at=payload.generated_at,
            finish_status=payload.finish_status,
            lineage=lineage,
            epistemic_class=epistemic_class,
            usage=payload.usage,
            duration_ms=payload.duration_ms,
            eval_result=eval_result,
        )

    def _validate_request(self, request: ModelInvocationRequest) -> None:
        try:
            require_model_ref_identity(request.model_ref)
        except ModelInvocationDomainError as exc:
            raise ModelInvocationError(INVALID_REQUEST, str(exc)) from exc
        if not request.task_purpose_id.strip():
            raise ModelInvocationError(INVALID_REQUEST, "task_purpose_id is required")
        if not request.expected_fields:
            raise ModelInvocationError(INVALID_REQUEST, "expected_fields is required")
        if request.timeout_seconds <= 0 or request.timeout_seconds > MAX_TIMEOUT_SECONDS:
            raise ModelInvocationError(
                INVALID_REQUEST,
                f"timeout_seconds must be in (0, {MAX_TIMEOUT_SECONDS}]",
            )
        if len(request.input_text) > MAX_INPUT_CHARS:
            raise ModelInvocationError(INVALID_REQUEST, "input_text exceeds bound")
        payload: dict[str, Any] = {
            "input_text": request.input_text,
            **dict(request.untrusted_external_metadata),
        }
        try:
            guard_invocation_payload(payload)
        except (ModelInvocationDomainError, ValueError) as exc:
            raise ModelInvocationError(INVALID_REQUEST, str(exc)) from exc

    def _enforce_exposure_policy(self) -> None:
        if self._port.exposure_class is not ProviderExposureClass.TEST_ONLY:
            raise ModelInvocationError(
                POLICY_EXPOSURE_DENIED,
                "real model call blocked: DÉLIA provider exposure policy is not proven",
            )
        if self._port.adapter_kind != "TEST_ONLY":
            raise ModelInvocationError(
                POLICY_EXPOSURE_DENIED,
                "real provider adapter is blocked by external configuration",
            )

    def _validate_structured_output(
        self,
        request: ModelInvocationRequest,
        structured_output: Mapping[str, Any],
    ) -> None:
        if not isinstance(structured_output, Mapping):
            raise ModelInvocationError(
                INVALID_STRUCTURED_OUTPUT,
                "structured output must be an object",
            )
        try:
            guard_invocation_payload(dict(structured_output))
        except (ModelInvocationDomainError, ValueError) as exc:
            raise ModelInvocationError(INVALID_STRUCTURED_OUTPUT, str(exc)) from exc
        missing = [field for field in request.expected_fields if field not in structured_output]
        if missing:
            raise ModelInvocationError(
                INVALID_STRUCTURED_OUTPUT,
                f"missing required fields: {', '.join(missing)}",
            )

    def _bind_eval(
        self,
        request: ModelInvocationRequest,
        configuration_lineage: ConfigurationLineage,
    ) -> EvalResult | None:
        bind = request.eval_bind
        if bind is None:
            return None
        identity = EvalIdentity(
            eval_id=bind.eval_id,
            evaluated_sha=bind.evaluated_sha,
            model_ref=request.model_ref,
            configuration_id=configuration_identity(configuration_lineage),
            instruction_version=request.instruction_lineage.version,
            fixture_id=bind.fixture_id,
            dataset_id=bind.dataset_id,
        )
        return EvalResult(
            identity=identity,
            outcome=EvalOutcome.PASS,
            observation="deterministic test-adapter foundation conformance only",
        )


def configuration_identity(lineage: ConfigurationLineage) -> str:
    material = "|".join(
        [
            lineage.model_ref.model_id,
            lineage.model_ref.version,
            lineage.model_ref.owner_ref,
            lineage.model_ref.provider_ref or "",
            lineage.instruction_lineage.instruction_id,
            lineage.instruction_lineage.version,
            lineage.instruction_lineage.content_hash,
            lineage.output_schema_id,
            lineage.output_schema_version,
            str(lineage.generation_config.max_output_units or ""),
            str(lineage.timeout_seconds or ""),
        ]
    )
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def safe_observability(
    *,
    invocation_id: str,
    model_ref: ModelRef,
    duration_ms: int | None,
    status: str,
    error_code: str | None = None,
    eval_id: str | None = None,
    input_units: int | None = None,
    output_units: int | None = None,
) -> dict[str, object]:
    """Safe operational metadata. No secrets, CoT, raw input, or Evidence text."""
    payload: dict[str, object] = {
        "invocation_id": invocation_id,
        "model_id": model_ref.model_id,
        "model_version": model_ref.version,
        "status": status,
    }
    if duration_ms is not None:
        payload["duration_ms"] = duration_ms
    if error_code:
        payload["error_code"] = error_code
    if eval_id:
        payload["eval_id"] = eval_id
    if input_units is not None:
        payload["input_units"] = input_units
    if output_units is not None:
        payload["output_units"] = output_units
    return payload


def model_result_authorizes_act(_result: ModelInvocationResult) -> bool:
    _ = recommendation_never_authorizes_act()
    return False


def eval_binds_to(
    result: EvalResult,
    *,
    model_ref: ModelRef,
    evaluated_sha: str,
    configuration_id: str,
) -> bool:
    identity = result.identity
    return (
        identity.model_ref == model_ref
        and identity.evaluated_sha == evaluated_sha
        and identity.configuration_id == configuration_id
    )
