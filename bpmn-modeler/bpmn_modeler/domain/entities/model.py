from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from .revision import Revision
from .working_copy import WorkingCopy

MAX_DISPLAY_NAME_LENGTH = 120


@dataclass(slots=True)
class Model:
    """Aggregate root: logical identity of a BPMN model.

    Holds exactly one WorkingCopy and the append-only Revision collection.
    Audit fields and the concurrency token are maintained by the
    Application/persistence layers and are not domain invariants.
    """

    id: str
    working_copy: WorkingCopy
    display_name: str
    version: int = 1
    archived_at: datetime | None = None
    revisions: list[Revision] = field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None
    created_by: str = ""
    updated_by: str = ""

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("model id must not be empty")
        self.display_name = _validated_display_name(self.display_name)
        if self.version < 1:
            raise ValueError("model version must be >= 1")
        if self.working_copy is None:
            raise ValueError("model requires exactly one working copy")

    @property
    def archived(self) -> bool:
        return self.archived_at is not None

    @property
    def latest_revision(self) -> Revision | None:
        if not self.revisions:
            return None
        return max(self.revisions, key=lambda revision: revision.revision_number)

    def rename(self, display_name: str) -> None:
        self.display_name = _validated_display_name(display_name)

    def archive(self, when: datetime) -> None:
        self.archived_at = when

    def unarchive(self) -> None:
        self.archived_at = None

    def append_revision(self, revision: Revision) -> None:
        if any(item.revision_number == revision.revision_number for item in self.revisions):
            raise ValueError("revision number must not be reused")
        self.revisions.append(revision)


def _validated_display_name(display_name: str) -> str:
    normalized = display_name.strip()
    if not normalized:
        raise ValueError("display name must not be empty")
    if len(normalized) > MAX_DISPLAY_NAME_LENGTH:
        raise ValueError("display name must be at most 120 characters")
    return normalized
