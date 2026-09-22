"""Deterministic invariants for model invocation lineage (C3-T3).

Reuses Evidence secret/CoT/injection guards. Does not invent a PrivacyEngine,
PromptRegistry, or automatic FACT promotion.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.domain.evidence.model import (
    AuthorityPolicySnapshot,
    EpistemicClass,
    ModelRef,
)
from app.domain.evidence.rules import (
    absorb_external_content_into_authority,
    assert_no_chain_of_thought,
    default_class_for_input_kind,
    reject_secret_bearing_payload,
)
from app.domain.model_invocation.model import ModelInvocationLineage


class ModelInvocationDomainError(ValueError):
    """Domain invariant violation for model invocation / lineage."""


_TOOL_EXECUTION_KEYS = frozenset(
    {
        "tool_calls",
        "function_call",
        "tool_call",
        "function_calls",
    }
)


def default_model_output_epistemic_class() -> EpistemicClass:
    """21 §4B.5: model_inference defaults to HYPOTHESIS, never FACT."""
    classified = default_class_for_input_kind("model_inference")
    if classified is not EpistemicClass.HYPOTHESIS:
        raise ModelInvocationDomainError("model_inference must default to HYPOTHESIS")
    return classified


def reject_automatic_fact_classification(epistemic_class: EpistemicClass) -> None:
    if epistemic_class is EpistemicClass.FACT:
        raise ModelInvocationDomainError(
            "model output must not automatically become FACT"
        )


def resolve_output_epistemic_class(
    declared: EpistemicClass | None,
    *,
    structured_output: Mapping[str, Any] | None = None,
) -> EpistemicClass:
    """Explicit class may be OBSERVATION/HYPOTHESIS/CONCLUSION/RECOMMENDATION.

    Model-claimed FACT in payload is ignored. Declared FACT is rejected.
    """
    if declared is EpistemicClass.FACT:
        raise ModelInvocationDomainError(
            "declared epistemic class FACT is forbidden for model output"
        )
    if structured_output is not None:
        claimed = structured_output.get("epistemic_class")
        if isinstance(claimed, str) and claimed.strip().upper() == EpistemicClass.FACT.value:
            # Provider/model claiming FACT does not qualify as FACT.
            return declared or default_model_output_epistemic_class()
    return declared or default_model_output_epistemic_class()


def lineage_grants_authorization(_lineage: ModelInvocationLineage) -> bool:
    return False


def model_ref_grants_permission(_model_ref: ModelRef) -> bool:
    return False


def recommendation_never_authorizes_act() -> bool:
    """RECOMMENDATION is never ACT authorization."""
    return False


def reject_tool_execution_payload(payload: Mapping[str, Any]) -> None:
    for key in payload:
        if str(key).lower() in _TOOL_EXECUTION_KEYS:
            raise ModelInvocationDomainError(
                f"tool execution field '{key}' is disabled in C3-T3"
            )


def guard_invocation_payload(payload: Mapping[str, Any]) -> None:
    reject_secret_bearing_payload(payload)
    assert_no_chain_of_thought(payload)
    reject_tool_execution_payload(payload)


def absorb_untrusted_into_authority(
    snapshot: AuthorityPolicySnapshot,
    untrusted: Mapping[str, Any],
) -> AuthorityPolicySnapshot:
    return absorb_external_content_into_authority(snapshot, untrusted)


def require_model_ref_identity(model_ref: ModelRef) -> None:
    if not model_ref.model_id.strip():
        raise ModelInvocationDomainError("ModelRef.model_id is required")
    if not model_ref.version.strip():
        raise ModelInvocationDomainError("ModelRef.version is required")
    if not model_ref.owner_ref.strip():
        raise ModelInvocationDomainError("ModelRef.owner_ref is required")
