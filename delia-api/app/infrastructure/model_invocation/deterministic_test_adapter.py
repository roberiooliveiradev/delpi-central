"""Deterministic TEST_ONLY adapter for ModelInvocationPort.

Not a production provider. Not proof of real-provider readiness.
"""

from __future__ import annotations

from datetime import datetime, timezone

from app.application.model_invocation.contracts import (
    ModelInvocationRequest,
    ProviderInvocationPayload,
)
from app.application.model_invocation.errors import (
    PROVIDER_REJECTED,
    PROVIDER_UNAVAILABLE,
    TIMEOUT,
    UNSUPPORTED_MODEL,
    ModelInvocationError,
)
from app.domain.model_invocation.model import (
    InvocationFinishStatus,
    ProviderExposureClass,
    UsageMetadata,
)


class DeterministicTestAdapter:
    """Infrastructure test double. adapter_kind is always TEST_ONLY."""

    ADAPTER_KIND = "TEST_ONLY"
    EXPOSURE_CLASS = ProviderExposureClass.TEST_ONLY

    def __init__(self, *, behavior: str = "success") -> None:
        self._behavior = behavior

    @property
    def adapter_kind(self) -> str:
        return self.ADAPTER_KIND

    @property
    def exposure_class(self) -> ProviderExposureClass:
        return self.EXPOSURE_CLASS

    def invoke(self, request: ModelInvocationRequest) -> ProviderInvocationPayload:
        generated_at = datetime.now(timezone.utc).isoformat()
        if self._behavior == "timeout":
            raise ModelInvocationError(TIMEOUT, "deterministic timeout")
        if self._behavior == "unavailable":
            raise ModelInvocationError(PROVIDER_UNAVAILABLE, "deterministic provider unavailable")
        if self._behavior == "rejected":
            raise ModelInvocationError(PROVIDER_REJECTED, "deterministic provider rejected")
        if self._behavior == "unsupported_model":
            raise ModelInvocationError(UNSUPPORTED_MODEL, "deterministic unsupported model")
        if self._behavior == "raw_exception":
            raise RuntimeError("sdk boom")
        if self._behavior == "missing_fields":
            return ProviderInvocationPayload(
                structured_output={"unrelated": True},
                generated_at=generated_at,
                usage=UsageMetadata(input_units=1, output_units=1, unit_kind="tokens"),
                duration_ms=3,
            )
        if self._behavior == "cot":
            return ProviderInvocationPayload(
                structured_output={
                    "answer": "x",
                    "chain_of_thought": "hidden",
                },
                generated_at=generated_at,
                duration_ms=4,
            )
        if self._behavior == "secret":
            return ProviderInvocationPayload(
                structured_output={
                    "answer": "x",
                    "api_key": "must-not-land",
                },
                generated_at=generated_at,
                duration_ms=4,
            )
        if self._behavior == "tool_calls":
            return ProviderInvocationPayload(
                structured_output={
                    "answer": "x",
                    "tool_calls": [{"name": "create_order"}],
                },
                generated_at=generated_at,
                duration_ms=4,
            )
        if self._behavior == "claim_fact":
            output = {field: "ok" for field in request.expected_fields}
            output["epistemic_class"] = "FACT"
            return ProviderInvocationPayload(
                structured_output=output,
                generated_at=generated_at,
                usage=UsageMetadata(input_units=2, output_units=3, unit_kind="tokens"),
                duration_ms=5,
            )

        if request.output_schema_id.startswith("c3t4."):
            return self._structured_understanding_payload(request, generated_at)

        output = {field: f"deterministic:{request.task_purpose_id}" for field in request.expected_fields}
        return ProviderInvocationPayload(
            structured_output=output,
            generated_at=generated_at,
            finish_status=InvocationFinishStatus.COMPLETED,
            usage=UsageMetadata(input_units=4, output_units=6, unit_kind="tokens"),
            duration_ms=7,
        )

    def _structured_understanding_payload(
        self,
        request: ModelInvocationRequest,
        generated_at: str,
    ) -> ProviderInvocationPayload:
        if self._behavior == "su_claim_fact":
            return ProviderInvocationPayload(
                structured_output={
                    "observations": [
                        {
                            "field_key": "machine_status",
                            "content": "Machine X stopped at 14:32",
                            "epistemic_class": "FACT",
                        }
                    ],
                    "limitations": [],
                    "conflict_present": False,
                },
                generated_at=generated_at,
                duration_ms=5,
            )
        if self._behavior == "su_conflict":
            return ProviderInvocationPayload(
                structured_output={
                    "observations": [
                        {
                            "field_key": "machine_status",
                            "content": "Machine X stopped at 14:32",
                            "epistemic_class": "OBSERVATION",
                        },
                        {
                            "field_key": "machine_status",
                            "content": "Machine X remained running at 14:32",
                            "epistemic_class": "OBSERVATION",
                        },
                    ],
                    "limitations": [{"code": "conflicting_evidence"}],
                    "conflict_present": True,
                },
                generated_at=generated_at,
                duration_ms=6,
            )
        if self._behavior == "su_missing":
            return ProviderInvocationPayload(
                structured_output={
                    "observations": [],
                    "limitations": [{"code": "insufficient_evidence"}],
                    "conflict_present": False,
                },
                generated_at=generated_at,
                duration_ms=4,
            )
        if self._behavior == "su_result_claim_fact":
            return ProviderInvocationPayload(
                structured_output={
                    "observations": [
                        {
                            "field_key": "machine_status",
                            "content": "Machine X stopped at 14:32",
                            "epistemic_class": "OBSERVATION",
                        }
                    ],
                    "epistemic_class": "FACT",
                    "limitations": [],
                    "conflict_present": False,
                },
                generated_at=generated_at,
                duration_ms=5,
            )
        if self._behavior == "su_invalid_schema":
            return ProviderInvocationPayload(
                structured_output={"answer": "not-observations"},
                generated_at=generated_at,
                duration_ms=3,
            )

        # Default positive: source-content observation extraction
        return ProviderInvocationPayload(
            structured_output={
                "observations": [
                    {
                        "field_key": "machine_status",
                        "content": "the source states that Machine X stopped at 14:32",
                        "epistemic_class": "OBSERVATION",
                        "limitations": [],
                    }
                ],
                "limitations": [],
                "conflict_present": False,
            },
            generated_at=generated_at,
            finish_status=InvocationFinishStatus.COMPLETED,
            usage=UsageMetadata(input_units=4, output_units=6, unit_kind="tokens"),
            duration_ms=7,
        )
