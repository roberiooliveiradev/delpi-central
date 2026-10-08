from __future__ import annotations

from typing import Protocol

from tm_app.domain.entities.process_bpmn_reference import ProcessBpmnReference


class ProcessBpmnReferenceRepositoryPort(Protocol):
    def process_exists(self, processo_id: str) -> bool: ...

    def get_active(self, processo_id: str) -> ProcessBpmnReference | None: ...

    def upsert(
        self,
        *,
        processo_id: str,
        bpmn_model_id: str,
        bpmn_revision_number: int,
        actor_user_id: str,
    ) -> tuple[ProcessBpmnReference, ProcessBpmnReference | None]:
        """Create or replace the active reference.

        Returns ``(current, previous)`` — ``previous`` is the replaced
        reference snapshot (for audit), or ``None`` when this was a first link.
        """
        ...

    def soft_delete(
        self,
        *,
        processo_id: str,
        actor_user_id: str,
    ) -> ProcessBpmnReference | None: ...
