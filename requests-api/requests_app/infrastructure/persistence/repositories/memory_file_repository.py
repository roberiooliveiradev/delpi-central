from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from requests_app.domain.entities.files import (
    RequestArtifact,
    RequestAttachment,
    RequestComment,
    RequestEvent,
)
from requests_app.domain.ports.file_repository_port import FileRepositoryPort


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class InMemoryFileRepository(FileRepositoryPort):
    def __init__(self) -> None:
        self.attachments: dict[str, RequestAttachment] = {}
        self.artifacts: dict[str, RequestArtifact] = {}
        self.events: list[RequestEvent] = []
        self.comments: list[RequestComment] = []

    def create_attachment(self, attachment: RequestAttachment) -> RequestAttachment:
        stored = deepcopy(attachment)
        stored.created_at = stored.created_at or _utcnow()
        self.attachments[str(stored.id)] = stored
        return deepcopy(stored)

    def get_attachment(self, attachment_id: UUID | str) -> RequestAttachment | None:
        found = self.attachments.get(str(attachment_id))
        return deepcopy(found) if found else None

    def list_attachments(self, request_id: UUID | str) -> list[RequestAttachment]:
        items = [
            item
            for item in self.attachments.values()
            if str(item.request_id) == str(request_id)
        ]
        items.sort(key=lambda row: row.created_at or _utcnow(), reverse=True)
        return [deepcopy(item) for item in items]

    def create_artifact(self, artifact: RequestArtifact) -> RequestArtifact:
        stored = deepcopy(artifact)
        stored.created_at = stored.created_at or _utcnow()
        self.artifacts[str(stored.id)] = stored
        return deepcopy(stored)

    def get_artifact(self, artifact_id: UUID | str) -> RequestArtifact | None:
        found = self.artifacts.get(str(artifact_id))
        return deepcopy(found) if found else None

    def list_artifacts(self, request_id: UUID | str) -> list[RequestArtifact]:
        items = [
            item
            for item in self.artifacts.values()
            if str(item.request_id) == str(request_id)
        ]
        items.sort(key=lambda row: row.created_at or _utcnow(), reverse=True)
        return [deepcopy(item) for item in items]

    def append_event(self, event: RequestEvent) -> RequestEvent:
        stored = deepcopy(event)
        stored.created_at = stored.created_at or _utcnow()
        if not stored.id:
            stored.id = uuid4()
        self.events.append(stored)
        return deepcopy(stored)

    def list_events(
        self,
        request_id: UUID | str,
        *,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[RequestEvent], int]:
        items = [e for e in self.events if str(e.request_id) == str(request_id)]
        items.sort(key=lambda row: row.created_at or _utcnow(), reverse=True)
        total = len(items)
        start = max(page - 1, 0) * page_size
        return [deepcopy(item) for item in items[start : start + page_size]], total

    def create_comment(self, comment: RequestComment) -> RequestComment:
        stored = deepcopy(comment)
        stored.created_at = stored.created_at or _utcnow()
        self.comments.append(stored)
        return deepcopy(stored)

    def list_comments(
        self,
        request_id: UUID | str,
        *,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[RequestComment], int]:
        items = [c for c in self.comments if str(c.request_id) == str(request_id)]
        items.sort(key=lambda row: row.created_at or _utcnow(), reverse=True)
        total = len(items)
        start = max(page - 1, 0) * page_size
        return [deepcopy(item) for item in items[start : start + page_size]], total
