"""C3-T7 decision-path routing contract value objects.

DecisionPath selects the smallest sufficient reasoning/decision path.
Path selection != authorization; != model invocation; != model routing.

Canonical semantics: 16 C3 DAG, 21 §4A.13, 17 §8, 23 §11.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.domain.evidence.model import EvidenceRef, SourceRef


class DecisionPath(str, Enum):
    """Canonical decision paths — smallest sufficient path wins.

    FAST       = deterministic rules/specifications with sufficient
                 authoritative context.
    OPERATIONAL = structured bounded context + deterministic
                 rules/calculations/reads; no model required in this slice.
    REASONING  = complex investigation/synthesis where smaller paths are
                 insufficient; a routing classification only, not a runtime.
    """

    FAST = "FAST"
    OPERATIONAL = "OPERATIONAL"
    REASONING = "REASONING"


class DecisionPathStatus(str, Enum):
    """Bounded routing outcome. Selection failure never defaults to a path."""

    SELECTED = "SELECTED"
    INCONCLUSIVE = "INCONCLUSIVE"  # required routing facts unknown
    BLOCKED = "BLOCKED"  # required routing facts/evidence known-absent


class RoutingReasonCode(str, Enum):
    """Bounded, deterministic, inspectable explanation codes — never CoT."""

    AUTHORITATIVE_RULE_APPLIES = "authoritative_rule_applies"
    STRUCTURED_CONTEXT_SUFFICIENT = "structured_context_sufficient"
    COMPLEX_INVESTIGATION_REQUIRED = "complex_investigation_required"
    EVIDENCE_CONFLICT_REQUIRES_INVESTIGATION = (
        "evidence_conflict_requires_investigation"
    )
    MISSING_ROUTING_FACTS = "missing_routing_facts"
    REQUIRED_EVIDENCE_MISSING = "required_evidence_missing"
    NO_SUFFICIENT_PATH = "no_sufficient_path"


@dataclass(frozen=True, slots=True)
class DecisionPathInput:
    """Minimal routing facts for deterministic path selection.

    None = unknown fact -> fail closed (INCONCLUSIVE).
    Intentionally excludes: user permission/RBAC, provider/model vendor,
    HTTP endpoint, UI route, tool selector, credentials/tokens.
    """

    request_class: str
    authoritative_deterministic_rule_available: bool | None = None
    authoritative_context_sufficient: bool | None = None
    structured_context_sufficient: bool | None = None
    complex_investigation_required: bool | None = None
    required_evidence_missing: bool | None = None
    evidence_conflict_present: bool | None = None
    evidence_refs: tuple[EvidenceRef, ...] = ()
    source_refs: tuple[SourceRef, ...] = ()

    def __post_init__(self) -> None:
        if not self.request_class.strip():
            raise ValueError("DecisionPathInput.request_class is required")


@dataclass(frozen=True, slots=True)
class DecisionPathResult:
    """Bounded routing result. Never permission, never model invocation."""

    selected_path: DecisionPath | None
    status: DecisionPathStatus
    reason_codes: tuple[RoutingReasonCode, ...] = ()
    required_evidence_refs: tuple[EvidenceRef, ...] = ()
    missing_evidence: bool = False
    limitations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.status is DecisionPathStatus.SELECTED:
            if self.selected_path is None:
                raise ValueError(
                    "DecisionPathResult.selected_path is required when SELECTED"
                )
        elif self.selected_path is not None:
            raise ValueError(
                "DecisionPathResult.selected_path must be absent unless SELECTED"
            )

    def grants_authorization(self) -> bool:
        return False

    def is_fact(self) -> bool:
        return False

    def invokes_model(self) -> bool:
        return False

    def selects_model(self) -> bool:
        return False
