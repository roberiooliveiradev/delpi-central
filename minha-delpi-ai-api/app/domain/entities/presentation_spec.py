"""PresentationSpec / PresentationIntent — gramática visual declarativa v1."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

PRESENTATION_SPEC_VERSION = 1

SUPPORTED_VIEWS = frozenset({"table", "chart", "kpi", "text", "tree", "auto"})
SUPPORTED_MARKS = frozenset(
    {
        "bar",
        "line",
        "area",
        "horizontal_bar",
        "donut",
        "pie",
        "grouped_bar",
        "stacked_bar",
        "combo",
        "scatter",
        "histogram",
        "heatmap",
        "gauge",
        "multi_line",
    }
)
SUPPORTED_PALETTE_FAMILIES = frozenset(
    {
        "brand",
        "sequential-blue",
        "cool",
        "warm",
        "diverging-status",
        "status",
    }
)
SUPPORTED_FORMATS = frozenset(
    {
        "currency",
        "percentage",
        "integer",
        "decimal",
        "date",
        "datetime",
        "duration",
        "quantity",
    }
)
SUPPORTED_ENCODING_CHANNELS = frozenset({"x", "y", "color", "size", "theta"})


@dataclass(frozen=True)
class PresentationIntent:
    """Intenção visual pré-execução (conceitos, não keys reais)."""

    view: str | None = None
    mark: str | None = None
    dimension_concepts: tuple[str, ...] = ()
    measure_concept: str | None = None
    palette_family: str | None = None
    sort_concept: str | None = None
    locale: str = "pt-BR"

    def as_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"locale": self.locale}
        if self.view:
            payload["view"] = self.view
        if self.mark:
            payload["mark"] = self.mark
        if self.dimension_concepts:
            payload["dimensionConcepts"] = list(self.dimension_concepts)
        if self.measure_concept:
            payload["measureConcept"] = self.measure_concept
        if self.palette_family:
            payload["paletteFamily"] = self.palette_family
        if self.sort_concept:
            payload["sortConcept"] = self.sort_concept
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any] | None) -> PresentationIntent:
        if not isinstance(payload, dict):
            return cls()
        dims = payload.get("dimensionConcepts") or payload.get("dimension_concepts") or []
        return cls(
            view=_norm_token(payload.get("view")),
            mark=_norm_token(payload.get("mark") or payload.get("chartType")),
            dimension_concepts=tuple(
                str(item).strip() for item in dims if str(item or "").strip()
            ),
            measure_concept=_norm_token(
                payload.get("measureConcept") or payload.get("measure_concept")
            ),
            palette_family=_norm_token(
                payload.get("paletteFamily") or payload.get("palette_family")
            ),
            sort_concept=_norm_token(
                payload.get("sortConcept") or payload.get("sort_concept")
            ),
            locale=str(payload.get("locale") or "pt-BR"),
        )


@dataclass(frozen=True)
class EncodingChannel:
    field: str
    type: str | None = None
    scale: str | None = None

    def as_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"field": self.field}
        if self.type:
            payload["type"] = self.type
        if self.scale:
            payload["scale"] = self.scale
        return payload

    @classmethod
    def from_dict(cls, payload: Any) -> EncodingChannel | None:
        if not isinstance(payload, dict):
            return None
        field_name = str(payload.get("field") or "").strip()
        if not field_name:
            return None
        return cls(
            field=field_name,
            type=_norm_token(payload.get("type")),
            scale=_norm_token(payload.get("scale")),
        )


@dataclass(frozen=True)
class PresentationSpec:
    """Proposta declarativa validável — nunca contrato de entrega MFE."""

    version: int = PRESENTATION_SPEC_VERSION
    view: str = "auto"
    mark: str | None = None
    encoding: dict[str, EncodingChannel] = field(default_factory=dict)
    fields: tuple[str, ...] = ()
    sort_field: str | None = None
    sort_direction: str | None = None
    labels: dict[str, str] = field(default_factory=dict)
    formats: dict[str, str] = field(default_factory=dict)
    palette_family: str | None = None
    legend_visible: bool | None = None
    provenance: str = "DETERMINISTIC"

    def as_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "version": self.version,
            "view": self.view,
            "provenance": self.provenance,
        }
        if self.mark:
            payload["mark"] = self.mark
        if self.encoding:
            payload["encoding"] = {
                channel: item.as_dict() for channel, item in self.encoding.items()
            }
        if self.fields:
            payload["fields"] = [{"field": key} for key in self.fields]
        if self.sort_field:
            payload["sort"] = {
                "field": self.sort_field,
                "direction": self.sort_direction or "desc",
            }
        if self.labels:
            payload["labels"] = dict(self.labels)
        if self.formats:
            payload["formats"] = dict(self.formats)
        if self.palette_family:
            payload["paletteFamily"] = self.palette_family
        if self.legend_visible is not None:
            payload["legend"] = {"visible": self.legend_visible}
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any] | None) -> PresentationSpec | None:
        if not isinstance(payload, dict):
            return None
        encoding_raw = payload.get("encoding") if isinstance(payload.get("encoding"), dict) else {}
        encoding: dict[str, EncodingChannel] = {}
        for channel, value in encoding_raw.items():
            token = str(channel or "").strip().lower()
            if token not in SUPPORTED_ENCODING_CHANNELS:
                continue
            parsed = EncodingChannel.from_dict(value)
            if parsed:
                encoding[token] = parsed

        fields_raw = payload.get("fields") or []
        fields: list[str] = []
        for item in fields_raw:
            if isinstance(item, dict):
                key = str(item.get("field") or "").strip()
            else:
                key = str(item or "").strip()
            if key:
                fields.append(key)

        sort_raw = payload.get("sort") if isinstance(payload.get("sort"), dict) else {}
        legend_raw = payload.get("legend") if isinstance(payload.get("legend"), dict) else {}
        labels = {
            str(key).strip(): str(value).strip()
            for key, value in dict(payload.get("labels") or {}).items()
            if str(key).strip() and str(value or "").strip()
        }
        formats = {
            str(key).strip(): str(value).strip()
            for key, value in dict(payload.get("formats") or {}).items()
            if str(key).strip() and str(value or "").strip()
        }

        return cls(
            version=int(payload.get("version") or PRESENTATION_SPEC_VERSION),
            view=_norm_token(payload.get("view")) or "auto",
            mark=_norm_token(payload.get("mark") or payload.get("chartType")),
            encoding=encoding,
            fields=tuple(fields),
            sort_field=str(sort_raw.get("field") or "").strip() or None,
            sort_direction=_norm_token(sort_raw.get("direction")),
            labels=labels,
            formats=formats,
            palette_family=_norm_token(
                payload.get("paletteFamily") or payload.get("palette_family")
            ),
            legend_visible=(
                bool(legend_raw.get("visible"))
                if "visible" in legend_raw
                else None
            ),
            provenance=str(payload.get("provenance") or "DETERMINISTIC").upper(),
        )


def _norm_token(value: Any) -> str | None:
    token = str(value or "").strip().lower()
    return token or None


# JSON Schema (structured outputs / contract tests) — additionalProperties false.
PRESENTATION_SPEC_JSON_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "additionalProperties": False,
    "required": ["version", "view"],
    "properties": {
        "version": {"type": "integer", "const": PRESENTATION_SPEC_VERSION},
        "view": {"type": "string", "enum": sorted(SUPPORTED_VIEWS)},
        "mark": {"type": ["string", "null"], "enum": sorted(SUPPORTED_MARKS) + [None]},
        "encoding": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                channel: {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["field"],
                    "properties": {
                        "field": {"type": "string", "minLength": 1, "maxLength": 128},
                        "type": {"type": ["string", "null"]},
                        "scale": {"type": ["string", "null"]},
                    },
                }
                for channel in sorted(SUPPORTED_ENCODING_CHANNELS)
            },
        },
        "fields": {
            "type": "array",
            "maxItems": 32,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["field"],
                "properties": {"field": {"type": "string", "minLength": 1, "maxLength": 128}},
            },
        },
        "sort": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "field": {"type": "string"},
                "direction": {"type": "string", "enum": ["asc", "desc"]},
            },
        },
        "labels": {
            "type": "object",
            "additionalProperties": {"type": "string", "maxLength": 120},
            "maxProperties": 64,
        },
        "formats": {
            "type": "object",
            "additionalProperties": {
                "type": "string",
                "enum": sorted(SUPPORTED_FORMATS),
            },
            "maxProperties": 64,
        },
        "paletteFamily": {
            "type": ["string", "null"],
            "enum": sorted(SUPPORTED_PALETTE_FAMILIES) + [None],
        },
        "legend": {
            "type": "object",
            "additionalProperties": False,
            "properties": {"visible": {"type": "boolean"}},
        },
        "provenance": {"type": "string"},
    },
}

PRESENTATION_INTENT_JSON_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "view": {"type": ["string", "null"], "enum": sorted(SUPPORTED_VIEWS) + [None]},
        "mark": {"type": ["string", "null"], "enum": sorted(SUPPORTED_MARKS) + [None]},
        "dimensionConcepts": {
            "type": "array",
            "maxItems": 8,
            "items": {"type": "string", "maxLength": 80},
        },
        "measureConcept": {"type": ["string", "null"], "maxLength": 80},
        "paletteFamily": {
            "type": ["string", "null"],
            "enum": sorted(SUPPORTED_PALETTE_FAMILIES) + [None],
        },
        "sortConcept": {"type": ["string", "null"], "maxLength": 80},
        "locale": {"type": "string", "default": "pt-BR"},
    },
}
