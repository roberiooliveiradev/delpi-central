from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol

from .artifact import CanonicalBpmnArtifact


class ValidationStage(str, Enum):
    INPUT_SAFETY = "input_safety"
    XML_WELL_FORMEDNESS = "xml_well_formedness"
    BPMN_STRUCTURE = "bpmn_structure"
    BPMN_SEMANTICS = "bpmn_semantics"
    BPMN_DI = "bpmn_di"
    PRODUCT_RULES = "product_rules"
    INTEGRATION_CONSTRAINTS = "integration_constraints"


class ValidationSeverity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class RuleSource(str, Enum):
    XML_W3C = "xml_w3c"
    OMG_BPMN = "omg_bpmn"
    OMG_BPMN_DI = "omg_bpmn_di"
    PRODUCT = "product"
    SECURITY = "security"
    INTEGRATION = "integration"


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    rule_id: str
    stage: ValidationStage
    source: RuleSource
    severity: ValidationSeverity
    message: str
    reference: str | None = None


@dataclass(frozen=True, slots=True)
class ValidationReport:
    evaluated_stages: frozenset[ValidationStage]
    not_evaluated_stages: frozenset[ValidationStage]
    issues: tuple[ValidationIssue, ...] = ()

    def __post_init__(self) -> None:
        overlap = self.evaluated_stages & self.not_evaluated_stages
        if overlap:
            raise ValueError("validation stages cannot be both evaluated and not evaluated")

        known_stages = frozenset(ValidationStage)
        classified_stages = self.evaluated_stages | self.not_evaluated_stages
        if classified_stages != known_stages:
            raise ValueError("validation report must classify every validation stage")

        if any(issue.stage not in self.evaluated_stages for issue in self.issues):
            raise ValueError("validation issues require an evaluated stage")


@dataclass(frozen=True, slots=True)
class InputSafetyEvidence:
    """Immutable evidence about the original input, produced at intake.

    `CanonicalBpmnArtifact.content` is an already-decoded string and cannot
    prove anything about the original bytes; this evidence is the only source
    for INPUT_SAFETY checks. Absence of evidence means the stage is
    NOT_EVALUATED — neither a pass nor a failure.
    """

    original_byte_length: int
    canonical_utf8_byte_length: int
    declared_encoding: str | None
    detected_encoding: str | None
    bom_present: bool
    decode_succeeded: bool
    dtd_detected: bool
    external_entity_declarations_detected: bool
    entity_expansion_beyond_builtins_detected: bool
    depth_within_limit: bool

    def has_security_violation(self) -> bool:
        return (
            not self.decode_succeeded
            or self.dtd_detected
            or self.external_entity_declarations_detected
            or self.entity_expansion_beyond_builtins_detected
            or not self.depth_within_limit
        )


class BpmnArtifactValidationPort(Protocol):
    def validate(
        self,
        artifact: CanonicalBpmnArtifact,
        evidence: InputSafetyEvidence | None = None,
    ) -> ValidationReport:
        """Assess an opaque canonical artifact and return validation evidence."""
        ...


class InputSafetyEvaluationPort(Protocol):
    def evaluate(self, evidence: InputSafetyEvidence) -> ValidationReport:
        """Evaluate the INPUT_SAFETY stage alone (intake path, no artifact)."""
        ...
