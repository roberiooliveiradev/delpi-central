from __future__ import annotations

import pytest

from bpmn_modeler.application.policy import RecognitionState, classify_recognition
from bpmn_modeler.application.validation import ValidationSeverity, ValidationStage
from bpmn_modeler.infrastructure.validation.engine import LxmlBpmnValidator
from bpmn_modeler.infrastructure.validation.intake import (
    MAX_INPUT_BYTES,
    intake_bytes,
)
from bpmn_modeler.domain.value_objects.canonical_bpmn_artifact import (
    CanonicalBpmnArtifact,
)

from . import fixtures as fx


def _classify(validator: LxmlBpmnValidator, content: bytes | str) -> tuple:
    raw = content.encode("utf-8") if isinstance(content, str) else content
    intake = intake_bytes(raw)
    if intake.artifact is None:
        report = validator.evaluate(intake.evidence)
    else:
        report = validator.validate(intake.artifact, intake.evidence)
    state = classify_recognition(
        report, decode_succeeded=intake.evidence.decode_succeeded
    )
    return state, report


def _rule_ids(report) -> set[str]:
    return {issue.rule_id for issue in report.issues}


@pytest.fixture(scope="module")
def validator():
    return LxmlBpmnValidator()


CASES = [
    ("FX-VALID-001", fx.FX_VALID_001, RecognitionState.BPMN_RECOGNIZED, set()),
    ("FX-VALID-002", fx.FX_VALID_002, RecognitionState.BPMN_RECOGNIZED, set()),
    ("FX-NODI-001", fx.FX_NODI_001, RecognitionState.BPMN_RECOGNIZED, {"BPMNDI-001"}),
    ("FX-NODI-002", fx.FX_NODI_002, RecognitionState.BPMN_RECOGNIZED_WITH_ISSUES, {"BPMNDI-007"}),
    ("FX-BADXML-001", fx.FX_BADXML_001, RecognitionState.MALFORMED_XML, {"XML-WF-001"}),
    ("FX-BADXML-002", fx.FX_BADXML_002, RecognitionState.MALFORMED_XML, {"XML-WF-001"}),
    ("FX-NOTBPMN-001", fx.FX_NOTBPMN_001, RecognitionState.XML_NOT_BPMN, {"BPMN-REC-001"}),
    ("FX-NS-001", fx.FX_NS_001, RecognitionState.XML_NOT_BPMN, {"BPMN-REC-002"}),
    ("FX-NS-002", fx.FX_NS_002, RecognitionState.BPMN_RECOGNIZED_WITH_ISSUES, {"BPMN-REC-004"}),
    ("FX-NS-003", fx.FX_NS_003, RecognitionState.MALFORMED_XML, {"XML-WF-NS-001"}),
    ("FX-SEC-001", fx.FX_SEC_001, RecognitionState.INPUT_REJECTED_SECURITY, {"SEC-DTD-001"}),
    ("FX-SEC-002", fx.FX_SEC_002, RecognitionState.INPUT_REJECTED_SECURITY, {"SEC-EXT-001", "SEC-DTD-001"}),
    ("FX-REC-001", fx.FX_REC_001, RecognitionState.BPMN_RECOGNIZED_INCOMPLETE, {"BPMN-REC-003"}),
    ("FX-DUP-001", fx.FX_DUP_001, RecognitionState.BPMN_RECOGNIZED_WITH_ISSUES, {"BPMN-STRUCT-002"}),
    ("FX-REF-001", fx.FX_REF_001, RecognitionState.BPMN_RECOGNIZED_WITH_ISSUES, {"BPMN-STRUCT-010"}),
    ("FX-REF-002", fx.FX_REF_002, RecognitionState.BPMN_RECOGNIZED_WITH_ISSUES, {"BPMN-STRUCT-011"}),
    ("FX-REF-003", fx.FX_REF_003, RecognitionState.BPMN_RECOGNIZED_WITH_ISSUES, {"BPMN-STRUCT-012"}),
    ("FX-REF-004", fx.FX_REF_004, RecognitionState.BPMN_RECOGNIZED_WITH_ISSUES, {"BPMN-STRUCT-014"}),
    ("FX-REF-005", fx.FX_REF_005, RecognitionState.BPMN_RECOGNIZED_WITH_ISSUES, {"BPMN-STRUCT-013"}),
    ("FX-REF-006", fx.FX_REF_006, RecognitionState.BPMN_RECOGNIZED_WITH_ISSUES, {"BPMN-STRUCT-015"}),
    ("FX-FLOW-001", fx.FX_FLOW_001, RecognitionState.BPMN_RECOGNIZED_WITH_ISSUES, {"BPMN-SEM-001"}),
    ("FX-FLOW-002", fx.FX_FLOW_002, RecognitionState.BPMN_RECOGNIZED_WITH_ISSUES, {"BPMN-SEM-002"}),
    ("FX-GW-001", fx.FX_GW_001, RecognitionState.BPMN_RECOGNIZED_WITH_ISSUES, {"BPMN-SEM-004"}),
    ("FX-GW-002", fx.FX_GW_002, RecognitionState.BPMN_RECOGNIZED_WITH_ISSUES, {"BPMN-SEM-003"}),
    ("FX-BND-001", fx.FX_BND_001, RecognitionState.BPMN_RECOGNIZED_WITH_ISSUES, {"BPMN-SEM-005"}),
    ("FX-LINK-001", fx.FX_LINK_001, RecognitionState.BPMN_RECOGNIZED_WITH_ISSUES, {"BPMN-SEM-006"}),
    ("FX-FLOW-003", fx.FX_FLOW_003, RecognitionState.BPMN_RECOGNIZED_WITH_ISSUES, {"BPMN-SEM-007"}),
    ("FX-FLOW-004", fx.FX_FLOW_004, RecognitionState.BPMN_RECOGNIZED_WITH_ISSUES, {"BPMN-SEM-008"}),
    ("FX-DI-001", fx.FX_DI_001, RecognitionState.BPMN_RECOGNIZED_WITH_ISSUES, {"BPMNDI-002"}),
    ("FX-DI-002", fx.FX_DI_002, RecognitionState.BPMN_RECOGNIZED_WITH_ISSUES, {"BPMNDI-003"}),
    ("FX-DI-003", fx.FX_DI_003, RecognitionState.BPMN_RECOGNIZED_WITH_ISSUES, {"BPMNDI-004"}),
    ("FX-DI-004", fx.FX_DI_004, RecognitionState.BPMN_RECOGNIZED_WITH_ISSUES, {"BPMNDI-008"}),
    ("FX-DI-005", fx.FX_DI_005, RecognitionState.BPMN_RECOGNIZED_WITH_ISSUES, {"BPMNDI-007"}),
    ("FX-DI-006", fx.FX_DI_006, RecognitionState.BPMN_RECOGNIZED_WITH_ISSUES, {"BPMNDI-005"}),
    ("FX-DI-007", fx.FX_DI_007, RecognitionState.BPMN_RECOGNIZED_WITH_ISSUES, {"BPMNDI-006", "BPMNDI-009"}),
    ("FX-PROD-001", fx.FX_PROD_001, RecognitionState.BPMN_RECOGNIZED_WITH_ISSUES, {"PROD-001"}),
    ("FX-PROD-002", fx.FX_PROD_002, RecognitionState.BPMN_RECOGNIZED_WITH_ISSUES, {"PROD-002"}),
    ("FX-EXT-001", fx.FX_EXT_001, RecognitionState.BPMN_RECOGNIZED_WITH_ISSUES, {"EXT-001"}),
    ("FX-EXT-002", fx.FX_EXT_002, RecognitionState.BPMN_RECOGNIZED_WITH_ISSUES, {"EXT-002"}),
    ("FX-EXT-003", fx.FX_EXT_003, RecognitionState.BPMN_RECOGNIZED_WITH_ISSUES, {"EXT-003"}),
    ("FX-EXT-004", fx.FX_EXT_004, RecognitionState.BPMN_RECOGNIZED_WITH_ISSUES, {"EXT-004", "EXT-001"}),
    ("FX-PRESERVE-001", fx.FX_PRESERVE_001, RecognitionState.BPMN_RECOGNIZED_WITH_ISSUES, set()),
]


@pytest.mark.parametrize("fixture_id,content,expected_state,expected_rules", CASES, ids=[c[0] for c in CASES])
def test_fixture_matrix(validator, fixture_id, content, expected_state, expected_rules):
    state, report = _classify(validator, content)
    assert state == expected_state, (
        f"{fixture_id}: expected {expected_state}, got {state}; "
        f"issues={_rule_ids(report)}"
    )
    missing = expected_rules - _rule_ids(report)
    assert not missing, f"{fixture_id}: missing rules {missing}; got {_rule_ids(report)}"
    assert ValidationStage.INTEGRATION_CONSTRAINTS in report.not_evaluated_stages


def test_oversize_input_is_security_rejection(validator):
    raw = b"<" + b"a" * (MAX_INPUT_BYTES + 1)
    intake = intake_bytes(raw)
    assert intake.oversized
    report = validator.evaluate(intake.evidence)
    assert "SEC-SIZE-001" in _rule_ids(report)
    state = classify_recognition(report, decode_succeeded=True)
    assert state == RecognitionState.INPUT_REJECTED_SECURITY


def test_deep_nesting_rejected(validator):
    depth = 200
    inner = "x"
    raw = "".join(f"<n{i}>" for i in range(depth)) + inner + "".join(
        f"</n{i}>" for i in reversed(range(depth))
    )
    intake = intake_bytes(raw.encode())
    report = validator.evaluate(intake.evidence)
    assert "SEC-DEPTH-001" in _rule_ids(report)


def test_undecodable_input_is_non_xml(validator):
    raw = b"\x89PNG\r\n\x1a\n" + bytes(range(256))
    intake = intake_bytes(raw)
    report = validator.evaluate(intake.evidence)
    state = classify_recognition(
        report, decode_succeeded=intake.evidence.decode_succeeded
    )
    assert state in (RecognitionState.NON_XML, RecognitionState.INPUT_REJECTED_SECURITY)


def test_entity_expansion_rejected(validator):
    raw = (
        '<?xml version="1.0"?><!DOCTYPE d [<!ENTITY a "x"><!ENTITY b "&a;&a;">]>'
        f'<bpmn:definitions xmlns:bpmn="{fx.BPMN_NS}" id="d" targetNamespace="urn:x">'
        "&b;</bpmn:definitions>"
    )
    intake = intake_bytes(raw.encode())
    report = validator.evaluate(intake.evidence)
    assert "SEC-ENT-001" in _rule_ids(report)


def test_report_issue_ordering_is_deterministic(validator):
    raw = fx.FX_VALID_001.encode()
    intake = intake_bytes(raw)
    r1 = validator.validate(intake.artifact, intake.evidence)
    r2 = validator.validate(intake.artifact, intake.evidence)
    assert [i.rule_id for i in r1.issues] == [i.rule_id for i in r2.issues]


def test_persisted_artifact_without_evidence(validator):
    """Persisted artifact: INPUT_SAFETY NOT_EVALUATED, other stages evaluated."""
    report = validator.validate(CanonicalBpmnArtifact(fx.FX_VALID_001))
    assert ValidationStage.INPUT_SAFETY in report.not_evaluated_stages
    assert ValidationStage.BPMN_STRUCTURE in report.evaluated_stages
    assert classify_recognition(report) == RecognitionState.BPMN_RECOGNIZED


def test_reference_conventions(validator):
    _, report = _classify(validator, fx.FX_REF_001)
    issue = next(i for i in report.issues if i.rule_id == "BPMN-STRUCT-010")
    assert issue.reference == "element:F1"
    _, report = _classify(validator, fx.FX_NS_002)
    xsd = next(i for i in report.issues if i.rule_id == "BPMN-STRUCT-001")
    assert xsd.reference.startswith("xml:")
