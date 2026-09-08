"""Contrato estável de rótulos de campo resolvidos (tabela, insight, síntese)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


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
        return str(self.source_by_key.get(str(key or "").strip()) or "").strip()

    def as_metadata(self) -> dict[str, Any]:
        return {
            "labels": dict(self.labels),
            "formats": dict(self.formats),
            "sourceByKey": dict(self.source_by_key),
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
            str(key).strip(): str(value).strip()
            for key, value in sources_raw.items()
            if str(key).strip() and str(value or "").strip()
        }
        return cls(labels=labels, formats=formats, source_by_key=source_by_key)

    def merge_labels(
        self,
        extra: Mapping[str, str] | None,
        *,
        source: str = "presentation",
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
            labels[token] = label
            sources[token] = source
        return FieldLabelBundle(
            labels=labels,
            formats=dict(self.formats),
            source_by_key=sources,
        )
