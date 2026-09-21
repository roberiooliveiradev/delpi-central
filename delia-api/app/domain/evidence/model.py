"""Evidence epistemic value objects — C3-T1 frozen semantics as domain model.

Canonical classes and linkage rules: docs/12-roadmap-e-evolucao/delia/21 §4B.
Refs reuse C0.S3 shared reference semantics (no parallel primitives).
C3-T2R1: SourceRef is identity/origin only (no authority field on the shared ref).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class EpistemicClass(str, Enum):
    """Canonical epistemic classes (not Prediction/Simulation)."""

    OBSERVATION = "OBSERVATION"
    FACT = "FACT"
    CALCULATION = "CALCULATION"
    HYPOTHESIS = "HYPOTHESIS"
    CONCLUSION = "CONCLUSION"
    RECOMMENDATION = "RECOMMENDATION"


class TypedResultKind(str, Enum):
    """Sole canonical discriminator for typed results outside EpistemicClass."""

    PREDICTION = "PREDICTION"
    SIMULATION = "SIMULATION"


class FreshnessClass(str, Enum):
    CURRENT_LIVE = "current/live"
    SNAPSHOT = "snapshot"
    CACHED_VALID = "cached-valid"
    STALE = "stale"
    UNKNOWN = "unknown"


class EvidencePresence(str, Enum):
    """Presence of evidence about a proposition — missing ≠ false."""

    PRESENT = "PRESENT"
    MISSING = "MISSING"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class SourceRef:
    """Identifiable origin reference only.

    SourceRef != source authority itself.
    SourceRef != source-access grant.
    Proposition authority is an external qualification input, not a SourceRef field.
    """

    source_id: str
    source_system: str
    provider_name: str | None = None
    revision: str | None = None
    observed_at: str | None = None

    def __post_init__(self) -> None:
        if not self.source_id.strip():
            raise ValueError("SourceRef.source_id is required")
        if not self.source_system.strip():
            raise ValueError("SourceRef.source_system is required")


@dataclass(frozen=True, slots=True)
class EvidenceRef:
    """Reference to a coordinated Evidence item. Not SoT. Not authorization."""

    evidence_id: str

    def __post_init__(self) -> None:
        if not self.evidence_id.strip():
            raise ValueError("EvidenceRef.evidence_id is required")


@dataclass(frozen=True, slots=True)
class EntityRef:
    entity_type: str
    entity_id: str
    source_system: str
    label: str | None = None
    revision: str | None = None


@dataclass(frozen=True, slots=True)
class ModelRef:
    model_id: str
    version: str
    owner_ref: str
    provider_ref: str | None = None
    family: str | None = None


@dataclass(frozen=True, slots=True)
class PredictionRef:
    prediction_id: str
    model_ref: ModelRef
    subject_entity_refs: tuple[EntityRef, ...] = ()
    target: str | None = None
    horizon: str | None = None
    freshness: FreshnessClass = FreshnessClass.UNKNOWN


@dataclass(frozen=True, slots=True)
class ScenarioRef:
    scenario_id: str
    version: str | None = None


@dataclass(frozen=True, slots=True)
class PredictionResult:
    """Typed PREDICTION result — Prediction ≠ FACT."""

    prediction_ref: PredictionRef
    value: Any = None
    kind: TypedResultKind = field(default=TypedResultKind.PREDICTION, init=False)

    def is_fact(self) -> bool:
        return False


@dataclass(frozen=True, slots=True)
class SimulationResult:
    """Typed SIMULATION result — SIMULATE ≠ APPLY; not current FACT."""

    scenario_ref: ScenarioRef
    mode: str = "SIMULATE"
    value: Any = None
    kind: TypedResultKind = field(default=TypedResultKind.SIMULATION, init=False)

    def __post_init__(self) -> None:
        if self.mode != "SIMULATE":
            raise ValueError("SimulationResult.mode must be SIMULATE (SIMULATE != APPLY)")

    def is_fact(self) -> bool:
        return False

    def authorizes_apply(self) -> bool:
        return False


@dataclass(frozen=True, slots=True)
class FactQualificationCriteria:
    """Epistemic FACT qualification inputs.

    Deliberately excludes current-user live AuthZ.
    FACT_STATUS != ACCESS_PERMISSION.
    source_authoritative_for_proposition is external deterministic input —
    not an intrinsic SourceRef property.
    """

    source_identifiable: bool
    source_authoritative_for_proposition: bool
    source_contract_validated: bool
    freshness_sufficient: bool
    explicit_fact_class: bool
    limitations_preserved: bool
    contains_secret_or_token: bool = False


@dataclass(frozen=True, slots=True)
class EvidenceItem:
    """Coordinated claim about the world — not the source system of truth."""

    evidence_ref: EvidenceRef
    epistemic_class: EpistemicClass
    proposition: str
    source_ref: SourceRef | None = None
    freshness: FreshnessClass = FreshnessClass.UNKNOWN
    limitations: tuple[str, ...] = ()
    entity_refs: tuple[EntityRef, ...] = ()
    derived_from: tuple[EvidenceRef, ...] = ()
    source_lineage: tuple[SourceRef, ...] = ()
    model_ref: ModelRef | None = None
    prediction_ref: PredictionRef | None = None
    transformation_kind: str | None = None
    presence: EvidencePresence = EvidencePresence.PRESENT

    def __post_init__(self) -> None:
        if not self.proposition.strip() and self.presence is EvidencePresence.PRESENT:
            raise ValueError("EvidenceItem.proposition is required when PRESENT")


@dataclass(frozen=True, slots=True)
class EvidenceConflictSet:
    """Explicit conflict among Evidence items — no fabricated reconciliation."""

    items: tuple[EvidenceItem, ...]
    reconciled: bool = False

    def __post_init__(self) -> None:
        if self.reconciled:
            raise ValueError(
                "EvidenceConflictSet must not fabricate reconciliation without Policy owner"
            )


@dataclass(frozen=True, slots=True)
class AuthorityPolicySnapshot:
    """Bounded authority/policy surface for injection-resistance tests."""

    policy_ids: tuple[str, ...] = ()
    rbac_permission_codes: tuple[str, ...] = ()
