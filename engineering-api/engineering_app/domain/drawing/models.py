"""Modelo canônico de evidências e relatório de análise de desenho
técnico — independente de SDKs de OCR/VLM e de frameworks (Documento 69
§11/§14). Domain layer puro: dataclasses + enums, sem pydantic.

Separação obrigatória: DRAWING_EVIDENCE ≠ OFFICIAL_BOM_FACT. Toda
informação carrega proveniência, classificação e limitações — a EVA
nunca converte hipótese em fato oficial nem emite aprovação técnica.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any


class EvidenceClass(StrEnum):
    OBSERVED = "OBSERVED"
    CALCULATED = "CALCULATED"
    INFERRED = "INFERRED"
    UNKNOWN = "UNKNOWN"


class VerificationStatus(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    WARNING = "WARNING"
    INCONCLUSIVE = "INCONCLUSIVE"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    NOT_CHECKED = "NOT_CHECKED"


class ReportStatus(StrEnum):
    DRAFT = "DRAFT"
    CANDIDATE = "CANDIDATE"


@dataclass
class DrawingEvidence:
    document_ref: str
    source: str
    evidence_type: str
    extraction_method: str
    source_revision: str | None = None
    page: int | None = None
    region: str | None = None
    observed_value: str | None = None
    normalized_value: str | None = None
    unit: str | None = None
    confidence: str = "medium"
    classification: EvidenceClass = EvidenceClass.OBSERVED
    limitations: list[str] = field(default_factory=list)


@dataclass
class Finding:
    id: str
    category: str
    severity: str
    severity_reason: str
    rule: str
    rule_source: str
    evidence_page: int | None = None
    evidence_region: str | None = None
    official_value: Any = None
    observed_value: Any = None
    expected_value: Any = None
    divergence: str | None = None
    confidence: str = "medium"
    limitations: list[str] = field(default_factory=list)
    recommended_correction: str | None = None
    reviewer: str = "Engenharia"


@dataclass
class Verification:
    key: str
    label: str
    status: VerificationStatus
    summary: str
    evidence_class: EvidenceClass = EvidenceClass.OBSERVED
    findings: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)


@dataclass
class DrawingAnalysisReport:
    identification: dict[str, Any]
    executive_summary: dict[str, Any]
    verifications: list[Verification]
    findings: list[Finding]
    status: ReportStatus = ReportStatus.DRAFT
    limitations: list[str] = field(default_factory=list)
    audit: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
