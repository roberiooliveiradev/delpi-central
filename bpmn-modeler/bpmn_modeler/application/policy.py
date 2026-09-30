from __future__ import annotations

import hashlib
from enum import Enum

from bpmn_modeler.domain.value_objects.canonical_bpmn_artifact import (
    CanonicalBpmnArtifact,
)

from .validation import (
    InputSafetyEvidence,
    RuleSource,
    ValidationIssue,
    ValidationReport,
    ValidationSeverity,
    ValidationStage,
)

STAGE_ORDER: tuple[ValidationStage, ...] = tuple(ValidationStage)
SOURCE_ORDER: tuple[RuleSource, ...] = tuple(RuleSource)


class RecognitionState(str, Enum):
    INPUT_REJECTED_SECURITY = "INPUT_REJECTED_SECURITY"
    NON_XML = "NON_XML"
    MALFORMED_XML = "MALFORMED_XML"
    XML_NOT_BPMN = "XML_NOT_BPMN"
    BPMN_RECOGNIZED_INCOMPLETE = "BPMN_RECOGNIZED_INCOMPLETE"
    BPMN_RECOGNIZED_WITH_ISSUES = "BPMN_RECOGNIZED_WITH_ISSUES"
    BPMN_RECOGNIZED = "BPMN_RECOGNIZED"


def artifact_checksum(artifact: CanonicalBpmnArtifact) -> str:
    return hashlib.sha256(artifact.content.encode("utf-8")).hexdigest()


def artifact_byte_length(artifact: CanonicalBpmnArtifact) -> int:
    return len(artifact.content.encode("utf-8"))


def sorted_issues(report: ValidationReport) -> tuple[ValidationIssue, ...]:
    return tuple(
        sorted(
            report.issues,
            key=lambda issue: (
                STAGE_ORDER.index(issue.stage),
                SOURCE_ORDER.index(issue.source),
                issue.rule_id,
                issue.reference is None,
                issue.reference or "",
            ),
        )
    )


def classify_recognition(
    report: ValidationReport,
    *,
    decode_succeeded: bool = True,
) -> RecognitionState:
    """Map a validation report to the frozen recognition state machine."""
    issues = report.issues

    def has_error_with_prefix(*prefixes: str) -> bool:
        return any(
            issue.severity is ValidationSeverity.ERROR
            and issue.rule_id.startswith(prefixes)
            for issue in issues
        )

    security_errors = [
        i for i in issues if i.rule_id.startswith("SEC-") and i.rule_id != "SEC-ENC-001"
    ]
    if any(i.severity is ValidationSeverity.ERROR for i in security_errors):
        return RecognitionState.INPUT_REJECTED_SECURITY
    if not decode_succeeded or has_error_with_prefix("SEC-ENC"):
        return RecognitionState.NON_XML
    if has_error_with_prefix("XML-WF"):
        return RecognitionState.MALFORMED_XML
    if has_error_with_prefix("BPMN-REC-001", "BPMN-REC-002"):
        return RecognitionState.XML_NOT_BPMN
    if any(i.rule_id == "BPMN-REC-003" for i in issues):
        return RecognitionState.BPMN_RECOGNIZED_INCOMPLETE
    non_absent_di_issues = [
        i
        for i in issues
        if not (i.rule_id == "BPMNDI-001" and i.severity is ValidationSeverity.INFO)
    ]
    if non_absent_di_issues:
        return RecognitionState.BPMN_RECOGNIZED_WITH_ISSUES
    return RecognitionState.BPMN_RECOGNIZED


IMPORTABLE_STATES = frozenset(
    {
        RecognitionState.BPMN_RECOGNIZED,
        RecognitionState.BPMN_RECOGNIZED_WITH_ISSUES,
        RecognitionState.BPMN_RECOGNIZED_INCOMPLETE,
    }
)


def import_allowed(state: RecognitionState) -> bool:
    return state in IMPORTABLE_STATES


def has_unsupported_mustunderstand(report: ValidationReport) -> bool:
    return any(issue.rule_id == "EXT-003" for issue in report.issues)


def save_allowed(state: RecognitionState, report: ValidationReport) -> bool:
    """Save is denied for non-recognized content and mustUnderstand capability failure."""
    return import_allowed(state) and not has_unsupported_mustunderstand(report)


def editing_allowed(report: ValidationReport) -> bool:
    return not has_unsupported_mustunderstand(report)
