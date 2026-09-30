"""Deterministic decision-path routing rules for C3-T7.

smallest sufficient path wins: FAST > OPERATIONAL > REASONING (sufficiency
order, not authority order). Missing facts fail closed; no default path;
no model invocation; no authorization.
"""

from __future__ import annotations

from app.domain.decision_path.model import (
    DecisionPath,
    DecisionPathInput,
    DecisionPathResult,
    DecisionPathStatus,
    RoutingReasonCode,
)

_ROUTING_FACT_NAMES = (
    "authoritative_deterministic_rule_available",
    "authoritative_context_sufficient",
    "structured_context_sufficient",
    "complex_investigation_required",
    "required_evidence_missing",
    "evidence_conflict_present",
)


def select_decision_path(request: DecisionPathInput) -> DecisionPathResult:
    """Select the smallest sufficient DecisionPath, or fail closed."""
    lineage = {"required_evidence_refs": request.evidence_refs}
    facts = {
        name: getattr(request, name) for name in _ROUTING_FACT_NAMES
    }
    if any(value is None for value in facts.values()):
        return DecisionPathResult(
            selected_path=None,
            status=DecisionPathStatus.INCONCLUSIVE,
            reason_codes=(RoutingReasonCode.MISSING_ROUTING_FACTS,),
            limitations=("required routing facts are unknown; no default path",),
            **lineage,
        )
    if request.required_evidence_missing:
        return DecisionPathResult(
            selected_path=None,
            status=DecisionPathStatus.BLOCKED,
            reason_codes=(RoutingReasonCode.REQUIRED_EVIDENCE_MISSING,),
            missing_evidence=True,
            limitations=("missing evidence != false; evidence not fabricated",),
            **lineage,
        )
    if (
        request.authoritative_deterministic_rule_available
        and request.authoritative_context_sufficient
    ):
        return DecisionPathResult(
            selected_path=DecisionPath.FAST,
            status=DecisionPathStatus.SELECTED,
            reason_codes=(RoutingReasonCode.AUTHORITATIVE_RULE_APPLIES,),
            limitations=(
                "authoritative deterministic rule takes priority over "
                "free-form model judgment",
            ),
            **lineage,
        )
    if request.evidence_conflict_present:
        return DecisionPathResult(
            selected_path=DecisionPath.REASONING,
            status=DecisionPathStatus.SELECTED,
            reason_codes=(
                RoutingReasonCode.EVIDENCE_CONFLICT_REQUIRES_INVESTIGATION,
            ),
            limitations=(
                "conflicting evidence preserved; no fabricated reconciliation",
            ),
            **lineage,
        )
    if (
        request.structured_context_sufficient
        and not request.complex_investigation_required
    ):
        return DecisionPathResult(
            selected_path=DecisionPath.OPERATIONAL,
            status=DecisionPathStatus.SELECTED,
            reason_codes=(RoutingReasonCode.STRUCTURED_CONTEXT_SUFFICIENT,),
            limitations=(
                "structured bounded context + deterministic rules/calculations; "
                "no model required",
            ),
            **lineage,
        )
    if request.complex_investigation_required:
        return DecisionPathResult(
            selected_path=DecisionPath.REASONING,
            status=DecisionPathStatus.SELECTED,
            reason_codes=(RoutingReasonCode.COMPLEX_INVESTIGATION_REQUIRED,),
            limitations=(
                "REASONING is a routing classification only; no reasoning "
                "runtime was executed",
            ),
            **lineage,
        )
    return DecisionPathResult(
        selected_path=None,
        status=DecisionPathStatus.BLOCKED,
        reason_codes=(RoutingReasonCode.NO_SUFFICIENT_PATH,),
        limitations=("no decision path proven sufficient; fail closed",),
        **lineage,
    )
