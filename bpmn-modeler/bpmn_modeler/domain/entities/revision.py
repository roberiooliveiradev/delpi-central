from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from ..value_objects.canonical_bpmn_artifact import CanonicalBpmnArtifact


class RevisionOrigin(str, Enum):
    EXPLICIT = "explicit"
    RESTORE = "restore"


@dataclass(frozen=True, slots=True)
class Revision:
    """Immutable snapshot of a model working copy at creation time."""

    revision_id: str
    revision_number: int
    artifact: CanonicalBpmnArtifact
    checksum: str
    created_at: datetime
    created_by: str
    origin: RevisionOrigin
    restored_from_revision_id: str | None = None
    name: str | None = None
    description: str | None = None
    created_by_name: str | None = None

    def __post_init__(self) -> None:
        if not self.revision_id.strip():
            raise ValueError("revision id must not be empty")
        if self.revision_number < 1:
            raise ValueError("revision number must be positive")
        if self.origin is RevisionOrigin.RESTORE and not self.restored_from_revision_id:
            raise ValueError("restore revision requires provenance")
        if self.name is not None:
            name = self.name.strip()
            if not name or len(name) > 120:
                raise ValueError("revision name must be 1..120 chars")
            object.__setattr__(self, "name", name)
        if self.description is not None and len(self.description) > 500:
            raise ValueError("revision description must be <= 500 chars")
