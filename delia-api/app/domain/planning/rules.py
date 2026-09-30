"""Deterministic plan-candidate validation rules for C3-T7.

Fail-closed against unknown capability ids, operation-character escalation
(e.g. untrusted READ -> ACT requests) and missing required evidence.
Validation does not invoke, prepare, execute or authorize anything.
"""

from __future__ import annotations

from app.domain.capability_catalog.model import CapabilityProjection
from app.domain.planning.model import (
    PlanCandidate,
    PlanValidationCode,
    PlanValidationResult,
)


def validate_plan_candidate(
    plan: PlanCandidate,
    available_capabilities: tuple[CapabilityProjection, ...],
) -> PlanValidationResult:
    """Validate a PlanCandidate against a bounded capability set.

    Unknown capability ids and semantic escalation fail closed. Steps are
    ordered; no dependency graph or cycle semantics exist in this slice.
    """
    by_id = {cap.capability_id: cap for cap in available_capabilities}
    errors: list[PlanValidationCode] = []
    seen_step_ids: set[str] = set()
    known_evidence = set(plan.evidence_refs)
    for step in plan.steps:
        if step.step_id in seen_step_ids:
            errors.append(PlanValidationCode.DUPLICATE_STEP_ID)
        seen_step_ids.add(step.step_id)
        capability = by_id.get(step.capability_id)
        if capability is None:
            errors.append(PlanValidationCode.UNKNOWN_CAPABILITY)
            continue
        if step.operation_character is not capability.operation_character:
            errors.append(PlanValidationCode.OPERATION_CHARACTER_MISMATCH)
        if any(ref not in known_evidence for ref in step.required_evidence_refs):
            errors.append(PlanValidationCode.MISSING_REQUIRED_EVIDENCE)
    return PlanValidationResult(
        valid=not errors,
        error_codes=tuple(errors),
        limitations=plan.limitations,
    )
