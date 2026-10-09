from __future__ import annotations

from typing import Protocol

from tm_app.domain.entities.process_bpmn_document import (
    ProcessBpmnDocument,
    ProcessBpmnRevision,
)


class ProcessBpmnDocumentRepositoryPort(Protocol):
    """Persistência do documento BPMN nativo por processo (G7).

    Concorrência: `version` inteiro crescente — toda escrita leva
    `expected_version` (o HTTP layer serializa como ETag If-Match).
    Revisões são imutáveis e append-only.
    """

    def process_exists(self, processo_id: str) -> bool: ...

    def get_active(self, processo_id: str) -> ProcessBpmnDocument | None: ...

    def has_active(self, processo_id: str) -> bool: ...

    def create(
        self,
        *,
        processo_id: str,
        working_copy_xml: str,
        working_copy_sha256: str,
        actor_user_id: str,
    ) -> ProcessBpmnDocument: ...

    def update_working_copy(
        self,
        *,
        document_id: str,
        working_copy_xml: str,
        working_copy_sha256: str,
        expected_version: int,
        actor_user_id: str,
    ) -> ProcessBpmnDocument | None:
        """Optimistic write. Returns the updated doc, or ``None`` on stale
        version (caller resolves 404-vs-409 by re-reading)."""
        ...

    def soft_delete(
        self,
        *,
        processo_id: str,
        actor_user_id: str,
    ) -> ProcessBpmnDocument | None: ...

    def list_revisions(self, document_id: str) -> list[ProcessBpmnRevision]: ...

    def get_revision(
        self,
        document_id: str,
        revision_number: int,
        *,
        with_artifact: bool = False,
    ) -> ProcessBpmnRevision | None: ...

    def get_latest_revision_number(self, document_id: str) -> int | None: ...

    def create_revision(
        self,
        *,
        document_id: str,
        artifact_xml: str,
        artifact_sha256: str,
        origin: str,
        restored_from_revision_id: str | None,
        name: str | None,
        description: str | None,
        actor_user_id: str,
        actor_name: str | None,
        expected_version: int,
    ) -> ProcessBpmnRevision | None:
        """Append-only checkpoint of the CURRENT working copy.

        Atomic under the document version guard — returns ``None`` on stale
        expected_version (409 semantics no caller)."""
        ...

    def restore_revision(
        self,
        *,
        document_id: str,
        revision_number: int,
        expected_version: int,
        actor_user_id: str,
        actor_name: str | None,
    ) -> tuple[ProcessBpmnDocument, ProcessBpmnRevision] | None:
        """working_copy ← artefato histórico + nova revisão origin='restore'
        com proveniência, numa única transação. ``None`` se stale/missing."""
        ...
