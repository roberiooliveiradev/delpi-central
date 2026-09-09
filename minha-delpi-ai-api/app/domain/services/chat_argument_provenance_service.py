"""Provenance de argumentos — rastreia origem sem substituir o OpenAPI validator."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

_SOURCES = frozenset(
    {
        "current_turn",
        "referenced_topic",
        "active_topic",
        "deterministic_extractor",
        "planner",
        "openapi_default",
    }
)


@dataclass(frozen=True)
class ArgumentProvenance:
    name: str
    value: Any
    source: str
    evidence_ref: str | None = None

    def as_dict(self) -> dict[str, Any]:
        payload = {
            "name": self.name,
            "value": self.value,
            "source": self.source if self.source in _SOURCES else "planner",
        }
        if self.evidence_ref:
            payload["evidenceRef"] = self.evidence_ref
        return payload


class ChatArgumentProvenanceService:
    @classmethod
    def annotate(
        cls,
        parameters: dict[str, Any] | None,
        *,
        source: str,
        evidence_ref: str | None = None,
        previous: list[dict[str, Any]] | None = None,
    ) -> list[dict[str, Any]]:
        rows = list(previous or [])
        by_name = {str(item.get("name") or ""): item for item in rows if isinstance(item, dict)}
        for name, value in (parameters or {}).items():
            key = str(name or "").strip()
            if not key or value in (None, ""):
                continue
            # Explicit current_turn always wins over stale provenance.
            if source == "current_turn" or key not in by_name:
                by_name[key] = ArgumentProvenance(
                    name=key,
                    value=value,
                    source=source,
                    evidence_ref=evidence_ref,
                ).as_dict()
        return list(by_name.values())

    @classmethod
    def merge_into_metadata(
        cls,
        metadata: dict[str, Any] | None,
        provenance: list[dict[str, Any]],
    ) -> dict[str, Any]:
        payload = dict(metadata or {})
        payload["argumentProvenance"] = provenance
        return payload
