"""Transformômetro-owned external reference to a BPMN model revision (G5).

The BPMN Modeler remains sole authority for models, working copies, revisions
and artifacts. This entity stores ONLY the external identity selected by the
user: (bpmn_model_id, bpmn_revision_number) — an immutable BPMN snapshot.

Never store BPMN XML/DI, working-copy snapshots, model display_name, revision
name or artifact checksum here — those are DERIVED / REMOTE READ data.
`Model.version` (working-copy concurrency token) is NOT a revision number and
must never be persisted as `bpmn_revision_number`.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if isinstance(value, datetime) else None


@dataclass
class ProcessBpmnReference:
    id: str
    processo_id: str
    bpmn_model_id: str
    bpmn_revision_number: int
    created_by_user_id: str
    updated_by_user_id: str
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "reference_id": self.id,
            "processo_id": self.processo_id,
            "model_id": self.bpmn_model_id,
            "revision_number": self.bpmn_revision_number,
            "created_by": self.created_by_user_id,
            "updated_by": self.updated_by_user_id,
            "created_at": _iso(self.created_at),
            "updated_at": _iso(self.updated_at),
        }

    def to_audit_dict(self) -> dict[str, Any]:
        return {
            "model_id": self.bpmn_model_id,
            "revision_number": self.bpmn_revision_number,
        }
