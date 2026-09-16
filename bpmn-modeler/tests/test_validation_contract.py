from typing import get_type_hints

import pytest

from bpmn_modeler.application import (
    BpmnArtifactValidationPort,
    RuleSource,
    ValidationIssue,
    ValidationReport,
    ValidationSeverity,
    ValidationStage,
)
from bpmn_modeler.domain import CanonicalBpmnArtifact


def _remaining_stages(*evaluated: ValidationStage) -> frozenset[ValidationStage]:
    return frozenset(ValidationStage) - frozenset(evaluated)


def test_validation_port_accepts_canonical_artifact_and_returns_report() -> None:
    hints = get_type_hints(BpmnArtifactValidationPort.validate)

    assert hints["artifact"] is CanonicalBpmnArtifact
    assert hints["return"] is ValidationReport


def test_report_distinguishes_evaluated_from_not_evaluated_stages() -> None:
    report = ValidationReport(
        evaluated_stages=frozenset({ValidationStage.XML_WELL_FORMEDNESS}),
        not_evaluated_stages=_remaining_stages(ValidationStage.XML_WELL_FORMEDNESS),
    )

    assert ValidationStage.XML_WELL_FORMEDNESS in report.evaluated_stages
    assert ValidationStage.INPUT_SAFETY in report.not_evaluated_stages
    assert ValidationStage.INPUT_SAFETY not in report.evaluated_stages


def test_report_requires_every_stage_to_be_explicitly_classified() -> None:
    with pytest.raises(ValueError, match="classify every validation stage"):
        ValidationReport(
            evaluated_stages=frozenset({ValidationStage.XML_WELL_FORMEDNESS}),
            not_evaluated_stages=frozenset(),
        )


def test_report_rejects_stage_marked_both_evaluated_and_not_evaluated() -> None:
    with pytest.raises(ValueError, match="both evaluated and not evaluated"):
        ValidationReport(
            evaluated_stages=frozenset({ValidationStage.INPUT_SAFETY}),
            not_evaluated_stages=frozenset(ValidationStage),
        )


def test_issue_preserves_validation_evidence() -> None:
    issue = ValidationIssue(
        rule_id="XML-WELL-FORMED",
        stage=ValidationStage.XML_WELL_FORMEDNESS,
        source=RuleSource.XML_W3C,
        severity=ValidationSeverity.ERROR,
        message="The XML payload could not be parsed.",
        reference="line:12",
    )

    assert issue.rule_id == "XML-WELL-FORMED"
    assert issue.stage is ValidationStage.XML_WELL_FORMEDNESS
    assert issue.source is RuleSource.XML_W3C
    assert issue.severity is ValidationSeverity.ERROR
    assert issue.message == "The XML payload could not be parsed."
    assert issue.reference == "line:12"


def test_report_preserves_multiple_issues_without_collapsing_to_boolean() -> None:
    issues = (
        ValidationIssue(
            rule_id="BPMN-REF-001",
            stage=ValidationStage.BPMN_STRUCTURE,
            source=RuleSource.OMG_BPMN,
            severity=ValidationSeverity.ERROR,
            message="A BPMN reference could not be resolved.",
        ),
        ValidationIssue(
            rule_id="PRODUCT-NAME-001",
            stage=ValidationStage.PRODUCT_RULES,
            source=RuleSource.PRODUCT,
            severity=ValidationSeverity.WARNING,
            message="A modeled element has no business label.",
        ),
    )
    evaluated = frozenset({ValidationStage.BPMN_STRUCTURE, ValidationStage.PRODUCT_RULES})

    report = ValidationReport(
        evaluated_stages=evaluated,
        not_evaluated_stages=frozenset(ValidationStage) - evaluated,
        issues=issues,
    )

    assert report.issues == issues
    assert len(report.issues) == 2


def test_issue_cannot_claim_evidence_for_a_not_evaluated_stage() -> None:
    issue = ValidationIssue(
        rule_id="INPUT-SAFETY-001",
        stage=ValidationStage.INPUT_SAFETY,
        source=RuleSource.SECURITY,
        severity=ValidationSeverity.INFO,
        message="Input safety evidence would require the original input boundary.",
    )

    with pytest.raises(ValueError, match="issues require an evaluated stage"):
        ValidationReport(
            evaluated_stages=frozenset({ValidationStage.XML_WELL_FORMEDNESS}),
            not_evaluated_stages=_remaining_stages(ValidationStage.XML_WELL_FORMEDNESS),
            issues=(issue,),
        )
