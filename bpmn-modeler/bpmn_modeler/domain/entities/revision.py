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

    def __post_init__(self) -> None:
        if not self.revision_id.strip():
            raise ValueError("revision id must not be empty")
        if self.revision_number < 1:
            raise ValueError("revision number must be positive")
        if self.origin is RevisionOrigin.RESTORE and not self.restored_from_revision_id:
            raise ValueError("restore revision requires provenance")
