"""Transformômetro-owned native BPMN document attached to a processo (G7).

The document is the single authority for the process-scoped BPMN artifact:
one active working copy per processo plus immutable append-only revisions —
the proven bpmn_modeler shape, inside the Transformômetro bounded context.

XOR (ADR-006): a processo either references an external BPMN Modeler model
(processo_bpmn_references, G5) or owns a native document — never both.
Enforcement lives in the application service, not in this entity.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if isinstance(value, datetime) else None


@dataclass
class ProcessBpmnDocument:
    id: str
    processo_id: str
    working_copy_xml: str
    working_copy_sha256: str
    version: int
    created_by_user_id: str
    updated_by_user_id: str
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "document_id": self.id,
            "processo_id": self.processo_id,
            "version": self.version,
            "working_copy_sha256": self.working_copy_sha256,
            "created_by": self.created_by_user_id,
            "updated_by": self.updated_by_user_id,
            "created_at": _iso(self.created_at),
            "updated_at": _iso(self.updated_at),
        }


@dataclass
class ProcessBpmnRevision:
    id: str
    document_id: str
    revision_number: int
    artifact_sha256: str
    origin: str  # "explicit" | "restore"
    restored_from_revision_id: str | None
    name: str | None
    description: str | None
    created_by_user_id: str
    created_by_name: str | None
    source_revision_number: int | None = None
    created_at: datetime | None = None
    artifact_xml: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "revision_id": self.id,
            "document_id": self.document_id,
            "revision_number": self.revision_number,
            "artifact_sha256": self.artifact_sha256,
            "origin": self.origin,
            "source_revision_number": self.source_revision_number,
            "name": self.name,
            "description": self.description,
            "created_by": self.created_by_user_id,
            "created_by_name": self.created_by_name,
            "created_at": _iso(self.created_at),
        }
