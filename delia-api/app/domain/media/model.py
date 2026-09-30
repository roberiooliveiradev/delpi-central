"""Multimodal/media Evidence foundation — provider-neutral domain values.

C3-MEDIA-FOUNDATION-01: media content is untrusted input; a multimodal
extraction is an OBSERVATION by default and never self-promotes to FACT.
No MediaRef is Evidence, Source authority, permission, or business fact.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum

from app.domain.evidence.model import (
    EntityRef,
    EpistemicClass,
    EvidenceRef,
    SourceRef,
)


class MediaKind(str, Enum):
    """Semantic media categories only — not file formats, not providers."""

    IMAGE = "IMAGE"
    AUDIO = "AUDIO"
    VIDEO = "VIDEO"
    SCREEN = "SCREEN"
    DOCUMENT_IMAGE = "DOCUMENT_IMAGE"


@dataclass(frozen=True, slots=True)
class MediaRef:
    """Provider-neutral media identity: id + kind + optional origin ref.

    Not a file path, URL, bucket, provider media id, camera id, codec, or
    extension — those are adapter mechanics and carry no authority here.
    MediaRef != Evidence automatically, != Source authority, != permission.
    """

    media_id: str
    kind: MediaKind
    source_ref: SourceRef | None = None

    def __post_init__(self) -> None:
        if not self.media_id.strip():
            raise ValueError("MediaRef.media_id is required")
        if not isinstance(self.kind, MediaKind):
            raise ValueError("MediaRef.kind must be MediaKind")
        if self.source_ref is not None and not isinstance(
            self.source_ref, SourceRef
        ):
            raise ValueError("MediaRef.source_ref must be SourceRef")


@dataclass(frozen=True, slots=True)
class MediaRegion:
    """Normalized bounded region inside one media frame.

    Region != recognized person, != canonical entity, != authorization,
    != business fact. Coordinates are normalized [0,1]; fail closed on
    negative/non-finite values, non-positive size, or out-of-range area.
    """

    x: float
    y: float
    width: float
    height: float

    def __post_init__(self) -> None:
        for name in ("x", "y", "width", "height"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(
                value, (int, float)
            ) or not math.isfinite(value):
                raise ValueError(f"MediaRegion.{name} must be finite number")
        if not (0.0 <= self.x <= 1.0):
            raise ValueError("MediaRegion.x must be within [0, 1]")
        if not (0.0 <= self.y <= 1.0):
            raise ValueError("MediaRegion.y must be within [0, 1]")
        if not (0.0 < self.width <= 1.0):
            raise ValueError("MediaRegion.width must be within (0, 1]")
        if not (0.0 < self.height <= 1.0):
            raise ValueError("MediaRegion.height must be within (0, 1]")
        if self.x + self.width > 1.0:
            raise ValueError("MediaRegion must not exceed frame bounds (x + width <= 1)")
        if self.y + self.height > 1.0:
            raise ValueError("MediaRegion must not exceed frame bounds (y + height <= 1)")


@dataclass(frozen=True, slots=True)
class MediaTimeRange:
    """Bounded provenance range inside one media artifact (seconds).

    Fail closed: no negative start, no end before start, no silent
    truncation or invented duration.
    """

    start_seconds: float
    end_seconds: float

    def __post_init__(self) -> None:
        for name in ("start_seconds", "end_seconds"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(
                value, (int, float)
            ) or not math.isfinite(value):
                raise ValueError(
                    f"MediaTimeRange.{name} must be finite number"
                )
        if self.start_seconds < 0.0:
            raise ValueError("MediaTimeRange.start_seconds must be >= 0")
        if self.end_seconds < self.start_seconds:
            raise ValueError(
                "MediaTimeRange.end_seconds must be >= start_seconds"
            )


@dataclass(frozen=True, slots=True)
class MediaObservation:
    """Typed multimodal observation — epistemically OBSERVATION only.

    Observation content (OCR-like text, captions, transcripts, provider
    descriptions, QR/barcode payloads) is untrusted data: it never mutates
    Policy, RBAC, Decision gates, CapabilityProjection, OperationCharacter,
    or ACT authorization. EntityRef entries are only references to already
    canonical entities — visibility in media never fabricates identity.
    """

    observation_id: str
    media_ref: MediaRef
    content: str
    epistemic_class: EpistemicClass = EpistemicClass.OBSERVATION
    evidence_refs: tuple[EvidenceRef, ...] = ()
    source_refs: tuple[SourceRef, ...] = ()
    entity_refs: tuple[EntityRef, ...] = ()
    region: MediaRegion | None = None
    time_range: MediaTimeRange | None = None
    confidence: float | None = None
    limitations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.observation_id.strip():
            raise ValueError("MediaObservation.observation_id is required")
        if not isinstance(self.media_ref, MediaRef):
            raise ValueError("MediaObservation.media_ref must be MediaRef")
        if not self.content.strip():
            raise ValueError("MediaObservation.content is required")
        if not isinstance(self.epistemic_class, EpistemicClass):
            raise ValueError(
                "MediaObservation.epistemic_class must be EpistemicClass"
            )
        if self.epistemic_class is not EpistemicClass.OBSERVATION:
            raise ValueError(
                "MediaObservation.epistemic_class must be OBSERVATION in "
                "this slice; FACT promotion requires a qualified-Fact "
                "contract, and higher classes are not admissible — fail closed"
            )
        if self.confidence is not None:
            if isinstance(self.confidence, bool) or not isinstance(
                self.confidence, (int, float)
            ) or not math.isfinite(self.confidence):
                raise ValueError(
                    "MediaObservation.confidence must be finite number"
                )
            if not (0.0 <= self.confidence <= 1.0):
                raise ValueError(
                    "MediaObservation.confidence must be within [0, 1]"
                )
        if self.region is not None and not isinstance(
            self.region, MediaRegion
        ):
            raise ValueError("MediaObservation.region must be MediaRegion")
        if self.time_range is not None and not isinstance(
            self.time_range, MediaTimeRange
        ):
            raise ValueError(
                "MediaObservation.time_range must be MediaTimeRange"
            )
        for name, expected in (
            ("evidence_refs", EvidenceRef),
            ("source_refs", SourceRef),
            ("entity_refs", EntityRef),
        ):
            for ref in getattr(self, name):
                if not isinstance(ref, expected):
                    raise ValueError(
                        f"MediaObservation.{name} entries must be "
                        f"{expected.__name__}"
                    )

    def grants_authorization(self) -> bool:
        return False

    def is_fact(self) -> bool:
        return False

    def is_official_quality_decision(self) -> bool:
        return False
