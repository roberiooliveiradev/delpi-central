"""C3-T4 Structured Understanding value objects.

Bounded source-observation extraction. Not a universal semantic graph,
Claim ontology, or Evidence store.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.evidence.model import EpistemicClass, EvidenceRef, SourceRef


@dataclass(frozen=True, slots=True)
class StructuredUnderstandingId:
    """C3-local result identity. Not a shared Ref primitive."""

    value: str

    def __post_init__(self) -> None:
        if not self.value.strip():
            raise ValueError("StructuredUnderstandingId.value is required")


@dataclass(frozen=True, slots=True)
class LimitationNote:
    """Bounded limitation/uncertainty note. Not CoT or hidden reasoning."""

    code: str
    detail: str | None = None

    def __post_init__(self) -> None:
        if not self.code.strip():
            raise ValueError("LimitationNote.code is required")


@dataclass(frozen=True, slots=True)
class StructuredObservation:
    """Observation about bounded source content — not a world FACT.

    Semantic meaning: the bounded source contains/states/represents `content`
    for `field_key`. Does not establish world truth.
    """

    field_key: str
    content: str
    epistemic_class: EpistemicClass = EpistemicClass.OBSERVATION
    evidence_refs: tuple[EvidenceRef, ...] = ()
    source_refs: tuple[SourceRef, ...] = ()
    limitations: tuple[LimitationNote, ...] = ()

    def __post_init__(self) -> None:
        if not self.field_key.strip():
            raise ValueError("StructuredObservation.field_key is required")
        if self.epistemic_class is EpistemicClass.FACT:
            raise ValueError(
                "StructuredObservation cannot be FACT; source observation != world FACT"
            )
        if self.epistemic_class is not EpistemicClass.OBSERVATION:
            raise ValueError(
                "C3-T4 source-observation slice allows only OBSERVATION per item"
            )

    def is_world_fact(self) -> bool:
        return False


@dataclass(frozen=True, slots=True)
class StructuredUnderstandingContent:
    """Minimal content model for source-observation extraction."""

    observations: tuple[StructuredObservation, ...]
    limitations: tuple[LimitationNote, ...] = ()
    conflict_present: bool = False
