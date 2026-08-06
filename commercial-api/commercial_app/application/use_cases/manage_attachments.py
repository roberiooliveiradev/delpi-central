from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import UUID

from commercial_app.application.services.attachment_storage import (
    AttachmentStorage,
    AttachmentStorageError,
)
from commercial_app.domain.entities.attachment import CommercialAttachment
from commercial_app.domain.ports.attachment_repository_port import AttachmentRepositoryPort
from commercial_app.domain.ports.seller_portfolio_repository_port import (
    SellerPortfolioRepositoryPort,
)
from commercial_app.domain.ports.task_repository_port import TaskRepositoryPort

ALLOWED_OWNER_TYPES = frozenset({"task"})


@dataclass(frozen=True)
class AttachmentFile:
    path: Path
    content_type: str
    file_name: str


class ManageAttachmentsUseCase:
    def __init__(
        self,
        *,
        repository: AttachmentRepositoryPort,
        storage: AttachmentStorage,
        task_repository: TaskRepositoryPort,
        portfolio_repository: SellerPortfolioRepositoryPort | None = None,
    ) -> None:
        self._repo = repository
        self._storage = storage
        self._tasks = task_repository
        self._portfolios = portfolio_repository

    def team_user_ids(self) -> set[str]:
        if self._portfolios is None:
            return set()
        return {
            str(item.user_id).strip()
            for item in self._portfolios.list_portfolios(active_only=True)
            if str(item.user_id or "").strip()
        }

    def _can_act_on_task(
        self,
        *,
        task: Any,
        actor_user_id: str,
        actor_is_portfolio_manager: bool,
    ) -> bool:
        actor = (actor_user_id or "").strip()
        if not actor:
            return False
        if (getattr(task, "created_by_user_id", None) or "").strip() == actor:
            return True
        if (getattr(task, "assignee_user_id", None) or "").strip() == actor:
            return True
        if not actor_is_portfolio_manager:
            return False
        assignee = (getattr(task, "assignee_user_id", None) or "").strip()
        return bool(assignee) and assignee in self.team_user_ids()

    def _assert_owner_access(
        self,
        *,
        owner_type: str,
        owner_id: str,
        actor_user_id: str,
        actor_is_portfolio_manager: bool,
    ) -> None:
        kind = (owner_type or "").strip().lower()
        oid = (owner_id or "").strip()
        if kind not in ALLOWED_OWNER_TYPES:
            raise ValueError("Tipo de vínculo de anexo não suportado.")
        if not oid:
            raise ValueError("owner_id é obrigatório.")
        if kind == "task":
            try:
                task_uuid = UUID(oid)
            except ValueError as exc:
                raise ValueError("owner_id de tarefa inválido.") from exc
            task = self._tasks.get_by_id(task_uuid)
            if task is None or task.status in {"cancelled"}:
                raise LookupError("Tarefa não encontrada.")
            if not self._can_act_on_task(
                task=task,
                actor_user_id=actor_user_id,
                actor_is_portfolio_manager=actor_is_portfolio_manager,
            ):
                raise PermissionError("Sem permissão para anexos desta tarefa.")

    def list(
        self,
        *,
        owner_type: str,
        owner_id: str,
        actor_user_id: str,
        actor_is_portfolio_manager: bool = False,
    ) -> list[CommercialAttachment]:
        self._assert_owner_access(
            owner_type=owner_type,
            owner_id=owner_id,
            actor_user_id=actor_user_id,
            actor_is_portfolio_manager=actor_is_portfolio_manager,
        )
        return list(
            self._repo.list_for_owner(
                owner_type=owner_type.strip().lower(),
                owner_id=owner_id.strip(),
            )
        )

    def counts_for_tasks(self, task_ids: list[str]) -> dict[str, int]:
        return self._repo.count_for_owners(owner_type="task", owner_ids=task_ids)

    def upload(
        self,
        *,
        owner_type: str,
        owner_id: str,
        original_name: str,
        content: bytes,
        mime_type: str | None,
        uploaded_by_user_id: str,
        actor_is_portfolio_manager: bool = False,
    ) -> CommercialAttachment:
        self._assert_owner_access(
            owner_type=owner_type,
            owner_id=owner_id,
            actor_user_id=uploaded_by_user_id,
            actor_is_portfolio_manager=actor_is_portfolio_manager,
        )
        kind = owner_type.strip().lower()
        oid = owner_id.strip()
        try:
            stored = self._storage.save(
                owner_type=kind,
                owner_id=oid,
                original_name=original_name,
                content=content,
                mime_type=mime_type,
            )
        except AttachmentStorageError:
            raise
        return self._repo.create(
            owner_type=kind,
            owner_id=oid,
            file_name=stored.file_name,
            storage_key=stored.storage_key,
            content_type=(mime_type or "application/octet-stream").split(";")[0].strip(),
            byte_size=stored.byte_size,
            uploaded_by_user_id=uploaded_by_user_id,
        )

    def get_file(
        self,
        *,
        attachment_id: UUID,
        actor_user_id: str,
        actor_is_portfolio_manager: bool = False,
    ) -> AttachmentFile:
        record = self._repo.get_by_id(attachment_id)
        if record is None:
            raise LookupError("Anexo não encontrado.")
        self._assert_owner_access(
            owner_type=record.owner_type,
            owner_id=record.owner_id,
            actor_user_id=actor_user_id,
            actor_is_portfolio_manager=actor_is_portfolio_manager,
        )
        path = self._storage.resolve_file(storage_key=record.storage_key)
        return AttachmentFile(
            path=path,
            content_type=record.content_type,
            file_name=record.file_name,
        )

    def delete(
        self,
        *,
        attachment_id: UUID,
        actor_user_id: str,
        actor_is_portfolio_manager: bool = False,
    ) -> dict[str, Any]:
        record = self._repo.get_by_id(attachment_id)
        if record is None:
            raise LookupError("Anexo não encontrado.")
        self._assert_owner_access(
            owner_type=record.owner_type,
            owner_id=record.owner_id,
            actor_user_id=actor_user_id,
            actor_is_portfolio_manager=actor_is_portfolio_manager,
        )
        deleted = self._repo.delete(attachment_id)
        if deleted is None:
            raise LookupError("Anexo não encontrado.")
        self._storage.delete(storage_key=record.storage_key)
        return {"deleted": True, "id": str(attachment_id)}
