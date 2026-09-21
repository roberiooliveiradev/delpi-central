from __future__ import annotations

from typing import Protocol

from tm_app.domain.entities.process_document import ProcessDocument


class ProcessDocumentRepositoryPort(Protocol):
    def process_exists(self, processo_id: str) -> bool: ...

    def list_by_processo(self, processo_id: str) -> list[ProcessDocument]: ...

    def get(self, *, processo_id: str, document_id: str) -> ProcessDocument | None: ...

    def create(
        self,
        *,
        processo_id: str,
        title: str,
        content_md: str,
        actor_user_id: str,
    ) -> ProcessDocument: ...

    def update(
        self,
        *,
        processo_id: str,
        document_id: str,
        title: str | None,
        content_md: str | None,
        actor_user_id: str,
    ) -> ProcessDocument | None: ...

    def soft_delete(
        self,
        *,
        processo_id: str,
        document_id: str,
        actor_user_id: str,
    ) -> ProcessDocument | None: ...
