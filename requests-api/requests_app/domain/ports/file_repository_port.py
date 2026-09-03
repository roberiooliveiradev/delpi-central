from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID

from requests_app.domain.entities.files import (
    RequestArtifact,
    RequestAttachment,
    RequestComment,
    RequestEvent,
)


class FileRepositoryPort(ABC):
    @abstractmethod
    def create_attachment(self, attachment: RequestAttachment) -> RequestAttachment: ...

    @abstractmethod
    def get_attachment(self, attachment_id: UUID | str) -> RequestAttachment | None: ...

    @abstractmethod
    def list_attachments(self, request_id: UUID | str) -> list[RequestAttachment]: ...

    @abstractmethod
    def create_artifact(self, artifact: RequestArtifact) -> RequestArtifact: ...

    @abstractmethod
    def get_artifact(self, artifact_id: UUID | str) -> RequestArtifact | None: ...

    @abstractmethod
    def list_artifacts(self, request_id: UUID | str) -> list[RequestArtifact]: ...

    @abstractmethod
    def append_event(self, event: RequestEvent) -> RequestEvent: ...

    @abstractmethod
    def list_events(
        self,
        request_id: UUID | str,
        *,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[RequestEvent], int]: ...

    @abstractmethod
    def create_comment(self, comment: RequestComment) -> RequestComment: ...

    @abstractmethod
    def list_comments(
        self,
        request_id: UUID | str,
        *,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[RequestComment], int]: ...
