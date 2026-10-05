"""C3-T7 structured planner contract value objects.

PlanCandidate describes semantic steps only — typed, deterministic,
non-executing. plan != execution; planned PREPARE != PREPARE;
planned ACT != ACT authorization/execution; planned VERIFY != Outcome.

Canonical semantics: 17 §7–§8, 21 §4A.13–§4A.15, 23 §11–§12.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.domain.capability_catalog.model import OperationCharacter
from app.domain.evidence.model import EvidenceRef, SourceRef


class PlanValidationCode(str, Enum):
    """Bounded deterministic validation codes — never CoT."""

    UNKNOWN_CAPABILITY = "unknown_capability"
    OPERATION_CHARACTER_MISMATCH = "operation_character_mismatch"
    MISSING_REQUIRED_EVIDENCE = "missing_required_evidence"
    DUPLICATE_STEP_ID = "duplicate_step_id"
    DUPLICATE_CAPABILITY_ID = "duplicate_capability_id"
    MAX_STEPS_EXCEEDED = "max_steps_exceeded"
    UNKNOWN_STEP_DEPENDENCY = "unknown_step_dependency"
    FORWARD_STEP_DEPENDENCY = "forward_step_dependency"


@dataclass(frozen=True, slots=True)
class PlanStep:
    """One ordered semantic step referencing a capability identity only.

    No execution mechanics: no HTTP method/path, no UI selector, no tool
    call syntax, no credentials. operation_character reuses the canonical
    C3-T5 vocabulary and must agree with the referenced CapabilityProjection.
    """

    step_id: str
    intent: str
    capability_id: str
    operation_character: OperationCharacter
    required_evidence_refs: tuple[EvidenceRef, ...] = ()
    expected_result: str | None = None
    expected_postcondition: str | None = None
    limitations: tuple[str, ...] = ()
    depends_on_step_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for name, value in (
            ("step_id", self.step_id),
            ("intent", self.intent),
            ("capability_id", self.capability_id),
        ):
            if not value.strip():
                raise ValueError(f"PlanStep.{name} is required")
        if not isinstance(self.operation_character, OperationCharacter):
            raise ValueError(
                "PlanStep.operation_character must be canonical OperationCharacter"
            )

    def grants_authorization(self) -> bool:
        return False

    def is_execution(self) -> bool:
        return False

    def authorizes_act(self) -> bool:
        return False

    def performs_prepare(self) -> bool:
        return False

    def verifies_outcome(self) -> bool:
        return False


@dataclass(frozen=True, slots=True)
class PlanCandidate:
    """Typed structured plan proposal. Never authorization or execution."""

    plan_id: str
    goal: str
    steps: tuple[PlanStep, ...] = ()
    evidence_refs: tuple[EvidenceRef, ...] = ()
    source_refs: tuple[SourceRef, ...] = ()
    limitations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for name, value in (
            ("plan_id", self.plan_id),
            ("goal", self.goal),
        ):
            if not value.strip():
                raise ValueError(f"PlanCandidate.{name} is required")

    def grants_authorization(self) -> bool:
        return False

    def is_execution(self) -> bool:
        return False

    def is_prepared(self) -> bool:
        return False

    def is_verified_outcome(self) -> bool:
        return False


@dataclass(frozen=True, slots=True)
class PlanValidationResult:
    """Bounded deterministic validation outcome — not an execution status."""

    valid: bool
    error_codes: tuple[PlanValidationCode, ...] = ()
    limitations: tuple[str, ...] = ()

    def grants_authorization(self) -> bool:
        return False
