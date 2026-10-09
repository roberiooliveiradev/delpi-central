"""Shared BPMN validation pipeline (G7 / ADR-006).

Pacote canônico Python — pure, sem dependência de repo/HTTP/DB — instalado
nos serviços que precisam validar artefatos BPMN 2.0 offline:
`bpmn-modeler` e `transformometro-api` (documento BPMN nativo do processo).

Superfície:

- ``CanonicalBpmnArtifact`` — payload XML opaco;
- ``ValidationStage/Severity/RuleSource/Issue/Report`` — tipos do relatório;
- ``InputSafetyEvidence`` — evidência de intake segura;
- ``LxmlBpmnValidator`` — engine offline (XSD OMG vendored + regras);
- ``intake_bytes`` — fronteira de intake segura (bytes → artefato);
- ``TemplateBlankArtifactFactory`` — artefato em branco governado.
"""

from .artifact import CanonicalBpmnArtifact
from .blank import IdGeneratorLike, TemplateBlankArtifactFactory
from .engine import LxmlBpmnValidator
from .intake import (
    MAX_CANONICAL_UTF8_BYTES,
    MAX_INPUT_BYTES,
    IntakeResult,
    intake_bytes,
)
from .types import (
    BpmnArtifactValidationPort,
    InputSafetyEvaluationPort,
    InputSafetyEvidence,
    RuleSource,
    ValidationIssue,
    ValidationReport,
    ValidationSeverity,
    ValidationStage,
)

__all__ = [
    "BpmnArtifactValidationPort",
    "CanonicalBpmnArtifact",
    "IdGeneratorLike",
    "InputSafetyEvaluationPort",
    "InputSafetyEvidence",
    "IntakeResult",
    "LxmlBpmnValidator",
    "MAX_CANONICAL_UTF8_BYTES",
    "MAX_INPUT_BYTES",
    "RuleSource",
    "TemplateBlankArtifactFactory",
    "ValidationIssue",
    "ValidationReport",
    "ValidationSeverity",
    "ValidationStage",
    "intake_bytes",
]
