"""PresentationDataProfile — perfil estatístico/semântico por campo tabular."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

SEMANTIC_TYPES = frozenset(
    {
        "quantitative",
        "temporal",
        "nominal",
        "ordinal",
        "identifier",
        "boolean",
        "unknown",
    }
)

CARDINALITY_BANDS = frozenset({"low", "medium", "high", "constant"})

LABEL_SOURCES = frozenset(
    {
        "OPENAPI_TITLE",
        "OPENAPI_DESCRIPTION",
        "METADATA_SCHEMA",
        "CANONICAL_VOCABULARY",
        "DETERMINISTIC_HUMANIZER",
        "LLM_LOCALIZATION",
        "LEGACY_FALLBACK",
    }
)


@dataclass(frozen=True)
class PresentationFieldProfile:
    key: str
    primitive_type: str
    semantic_type: str
    cardinality: int
    cardinality_band: str
    null_rate: float
    is_constant: bool
    is_dimension_candidate: bool
    is_measure_candidate: bool
    sensitive: bool = False
    display_label: str | None = None
    format: str | None = None
    label_source: str | None = None
    min_value: float | None = None
    max_value: float | None = None

    def as_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "key": self.key,
            "primitiveType": self.primitive_type,
            "semanticType": self.semantic_type,
            "cardinality": self.cardinality,
            "cardinalityBand": self.cardinality_band,
            "nullRate": self.null_rate,
            "isConstant": self.is_constant,
            "isDimensionCandidate": self.is_dimension_candidate,
            "isMeasureCandidate": self.is_measure_candidate,
            "sensitive": self.sensitive,
        }
        if self.display_label:
            payload["displayLabel"] = self.display_label
        if self.format:
            payload["format"] = self.format
        if self.label_source:
            payload["labelSource"] = self.label_source
        if self.min_value is not None:
            payload["min"] = self.min_value
        if self.max_value is not None:
            payload["max"] = self.max_value
        return payload


@dataclass(frozen=True)
class PresentationDataProfile:
    row_count: int
    sampled_row_count: int
    fields: tuple[PresentationFieldProfile, ...] = ()
    dimension_candidates: tuple[str, ...] = ()
    measure_candidates: tuple[str, ...] = ()
    temporal_candidates: tuple[str, ...] = ()
    profile_hash: str = ""
    resolved_field_labels: dict[str, Any] = field(default_factory=dict)

    def field_map(self) -> dict[str, PresentationFieldProfile]:
        return {item.key: item for item in self.fields}

    def as_dict(self) -> dict[str, Any]:
        return {
            "rowCount": self.row_count,
            "sampledRowCount": self.sampled_row_count,
            "fields": [item.as_dict() for item in self.fields],
            "dimensionCandidates": list(self.dimension_candidates),
            "measureCandidates": list(self.measure_candidates),
            "temporalCandidates": list(self.temporal_candidates),
            "profileHash": self.profile_hash,
            "resolvedFieldLabels": dict(self.resolved_field_labels),
        }
