"""Contrato estável de rótulos de campo resolvidos (tabela, insight, síntese)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

# Provenance tokens (§26-R). Legacy short names are mapped, never stored as new output.
CANONICAL_LABEL_SOURCES = frozenset(
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

_LEGACY_LABEL_SOURCES = {
    "meta": "METADATA_SCHEMA",
    "openapi": "OPENAPI_TITLE",
    "openapi_title": "OPENAPI_TITLE",
    "openapi_description": "OPENAPI_DESCRIPTION",
    "catalog": "CANONICAL_VOCABULARY",
    "profile": "METADATA_SCHEMA",
    "humanize": "DETERMINISTIC_HUMANIZER",
    "discovery": "LLM_LOCALIZATION",
    "llm": "LLM_LOCALIZATION",
    "legacy": "LEGACY_FALLBACK",
    "presentation": "LEGACY_FALLBACK",
}


def canonicalize_label_source(raw: str | None) -> str:
    token = str(raw or "").strip()
    if not token:
        return ""
    mapped = _LEGACY_LABEL_SOURCES.get(token.lower())
    if mapped:
        return mapped
    upper = token.upper()
    if upper in CANONICAL_LABEL_SOURCES:
        return upper
    return upper


@dataclass(frozen=True)
class FieldLabelBundle:
    """Mapa canônico key → rótulo PT, com formato e origem por chave."""

    labels: dict[str, str] = field(default_factory=dict)
    formats: dict[str, str] = field(default_factory=dict)
    source_by_key: dict[str, str] = field(default_factory=dict)

    def label_for(self, key: str, *, default: str | None = None) -> str:
        token = str(key or "").strip()
        if not token:
            return str(default or "")
        resolved = str(self.labels.get(token) or "").strip()
        if resolved:
            return resolved
        return str(default if default is not None else "")

    def source_for(self, key: str) -> str:
        return canonicalize_label_source(
            str(self.source_by_key.get(str(key or "").strip()) or "").strip()
        )

    def as_metadata(self) -> dict[str, Any]:
        return {
            "labels": dict(self.labels),
            "formats": dict(self.formats),
            "sourceByKey": {
                key: canonicalize_label_source(value)
                for key, value in self.source_by_key.items()
                if canonicalize_label_source(value)
            },
        }

    @classmethod
    def from_metadata(cls, payload: Mapping[str, Any] | None) -> FieldLabelBundle:
        if not isinstance(payload, Mapping):
            return cls()

        raw = payload.get("resolvedFieldLabels")
        if not isinstance(raw, Mapping):
            raw = payload if "labels" in payload or "sourceByKey" in payload else None
        if not isinstance(raw, Mapping):
            return cls()

        labels_raw = raw.get("labels") if isinstance(raw.get("labels"), Mapping) else {}
        formats_raw = raw.get("formats") if isinstance(raw.get("formats"), Mapping) else {}
        sources_raw = (
            raw.get("sourceByKey") if isinstance(raw.get("sourceByKey"), Mapping) else {}
        )

        labels = {
            str(key).strip(): str(value).strip()
            for key, value in labels_raw.items()
            if str(key).strip() and str(value or "").strip()
        }
        formats = {
            str(key).strip(): str(value).strip()
            for key, value in formats_raw.items()
            if str(key).strip() and str(value or "").strip()
        }
        source_by_key = {
            str(key).strip(): canonicalize_label_source(str(value).strip())
            for key, value in sources_raw.items()
            if str(key).strip() and canonicalize_label_source(str(value or "").strip())
        }
        return cls(labels=labels, formats=formats, source_by_key=source_by_key)

    def merge_labels(
        self,
        extra: Mapping[str, str] | None,
        *,
        source: str = "presentation",
        overwrite: bool = True,
    ) -> FieldLabelBundle:
        if not extra:
            return self
        labels = dict(self.labels)
        sources = dict(self.source_by_key)
        for key, value in extra.items():
            token = str(key or "").strip()
            label = str(value or "").strip()
            if not token or not label:
                continue
            if not overwrite and token in labels:
                continue
            labels[token] = label
            sources[token] = canonicalize_label_source(source) or "LEGACY_FALLBACK"
        return FieldLabelBundle(
            labels=labels,
            formats=dict(self.formats),
            source_by_key=sources,
        )
