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
from commercial_app.domain.entities.task import CommercialTask
from commercial_app.domain.ports.attachment_repository_port import AttachmentRepositoryPort
from commercial_app.domain.ports.interaction_message_repository_port import (
    InteractionMessageRepositoryPort,
)
from commercial_app.domain.ports.interaction_room_repository_port import (
    InteractionRoomRepositoryPort,
)
from commercial_app.domain.ports.seller_portfolio_repository_port import (
    SellerPortfolioRepositoryPort,
)
from commercial_app.domain.ports.task_repository_port import TaskRepositoryPort
from commercial_app.domain.services.interaction_room_content_service import (
    InteractionRoomContentService,
)

ALLOWED_OWNER_TYPES = frozenset({"task", "room_message"})


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
        rooms: InteractionRoomRepositoryPort | None = None,
        messages: InteractionMessageRepositoryPort | None = None,
    ) -> None:
        self._repo = repository
        self._storage = storage
        self._tasks = task_repository
        self._portfolios = portfolio_repository
        self._rooms = rooms
        self._messages = messages

    def team_user_ids(self) -> set[str]:
        if self._portfolios is None:
            return set()
        list_members = getattr(self._portfolios, "list_member_user_ids", None)
        if callable(list_members):
            return {
                str(uid).strip()
                for uid in list_members(active_portfolios_only=True)
                if str(uid or "").strip()
            }
        return {
            str(item.user_id).strip()
            for item in self._portfolios.list_portfolios(active_only=True)
            if str(item.user_id or "").strip()
        }

    def _can_act_on_task(
        self,
        *,
        task: CommercialTask,
        actor_user_id: str,
        actor_is_portfolio_manager: bool,
    ) -> bool:
        """Criador, qualquer responsável (multi) ou gestor da equipe do assignee."""
        actor = (actor_user_id or "").strip()
        if not actor:
            return False
        if (task.created_by_user_id or "").strip() == actor:
            return True
        assignees = task.resolved_assignee_user_ids()
        if actor in assignees:
            return True
        if not actor_is_portfolio_manager:
            return False
        team = self.team_user_ids()
        return any(uid in team for uid in assignees if uid)

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
            return
        if kind == "room_message":
            try:
                message_id = UUID(oid)
            except ValueError as exc:
                raise ValueError(
                    InteractionRoomContentService.error("attachmentOwnerInvalid")
                ) from exc
            if self._messages is None or self._rooms is None:
                raise PermissionError(InteractionRoomContentService.error("accessDenied"))
            message = self._messages.get_by_id(message_id)
            if message is None or message.deleted_at is not None:
                raise LookupError(InteractionRoomContentService.error("messageNotFound"))
            actor = (actor_user_id or "").strip()
            if self._rooms.get_member(room_id=message.room_id, user_id=actor) is None:
                raise PermissionError(InteractionRoomContentService.error("accessDenied"))
            return

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
        record = self._repo.create(
            owner_type=kind,
            owner_id=oid,
            file_name=stored.file_name,
            storage_key=stored.storage_key,
            content_type=(mime_type or "application/octet-stream").split(";")[0].strip(),
            byte_size=stored.byte_size,
            uploaded_by_user_id=uploaded_by_user_id,
        )
        if kind == "room_message":
            self._notify_room_attachment(
                record=record,
                actor_user_id=uploaded_by_user_id,
                reason="uploaded",
            )
        return record

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
        if record.owner_type.strip().lower() == "room_message":
            self._notify_room_attachment(
                record=record,
                actor_user_id=actor_user_id,
                reason="deleted",
            )
        return {"deleted": True, "id": str(attachment_id)}

    def _notify_room_attachment(
        self,
        *,
        record: CommercialAttachment,
        actor_user_id: str,
        reason: str,
    ) -> None:
        if self._messages is None or self._rooms is None:
            return
        try:
            from commercial_app.application.services.commercial_realtime_notify import (
                notify_interaction_attachment,
            )

            message = self._messages.get_by_id(UUID(record.owner_id))
            if message is None:
                return
            members = [
                item.user_id
                for item in self._rooms.list_members(message.room_id)
                if item.user_id
            ]
            notify_interaction_attachment(
                room_id=str(message.room_id),
                message_id=str(message.id),
                attachment_id=str(record.id),
                file_name=record.file_name,
                member_user_ids=members,
                actor_user_id=actor_user_id,
                reason=reason,
            )
        except Exception:  # noqa: BLE001 — notificação não pode falhar o anexo
            return
