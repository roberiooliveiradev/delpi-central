from __future__ import annotations

from typing import Any
from uuid import uuid4

from tm_app.application.security.authorization_policy import TransformometroAuthorizationPolicy
from tm_app.domain.entities.interaction_room import InteractionAttachment, InteractionMessage, InteractionRoom
from tm_app.domain.ports.interaction_room_repository_port import InteractionRoomRepositoryPort
from tm_app.domain.services.interaction_room_rules import (
    normalize_inbox_filter,
    normalize_mentions,
    normalize_message_content,
    normalize_processo_id,
    normalize_reaction_code,
    normalize_uuid,
)
from tm_app.domain.services.transformometro_task_rules import normalize_user_id
from tm_app.infrastructure.storage.interaction_attachment_storage import InteractionAttachmentStorage

DEFAULT_MESSAGE_LIMIT = 50
MAX_MESSAGE_LIMIT = 100


def _actor(user: Any) -> str:
    return normalize_user_id(str(getattr(user, "id", "") or ""), field="Usuário autenticado")


def _limit(value: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = DEFAULT_MESSAGE_LIMIT
    return max(1, min(parsed, MAX_MESSAGE_LIMIT))


class InteractionRoomUseCases:
    def __init__(
        self,
        repo: InteractionRoomRepositoryPort,
        policy: TransformometroAuthorizationPolicy | None = None,
        storage: InteractionAttachmentStorage | None = None,
    ) -> None:
        self._repo = repo
        self._policy = policy or TransformometroAuthorizationPolicy()
        self._storage = storage

    def open_for_process(self, user: Any, processo_id: str) -> InteractionRoom:
        self._policy.require_access(user)
        actor = _actor(user)
        room = self._repo.get_or_create(
            processo_id=normalize_processo_id(processo_id),
            created_by_user_id=actor,
        )
        if room is None:
            raise LookupError("Processo não encontrado.")
        confirmed = self._repo.get(room.id)
        if confirmed is None or confirmed.processo_id != room.processo_id:
            raise RuntimeError("OUTCOME_VERIFICATION_FAILED")
        return confirmed

    def get_room(self, user: Any, room_id: str) -> InteractionRoom:
        self._policy.require_access(user)
        room = self._repo.get(normalize_uuid(room_id, label="A sala"))
        if room is None:
            raise LookupError("Sala não encontrada.")
        return room

    def list_rooms(self, user: Any, *, inbox_filter: str = "all") -> list[InteractionRoom]:
        self._policy.require_access(user)
        return self._repo.list_rooms(
            viewer_user_id=_actor(user),
            inbox_filter=normalize_inbox_filter(inbox_filter),
        )

    def list_messages(
        self,
        user: Any,
        room_id: str,
        *,
        limit: int = DEFAULT_MESSAGE_LIMIT,
        before_id: str | None = None,
    ) -> dict[str, Any]:
        self._policy.require_access(user)
        room = self.get_room(user, room_id)
        cursor = normalize_uuid(before_id, label="A mensagem âncora") if before_id else None
        messages, has_more = self._repo.list_messages(
            room.id,
            limit=_limit(limit),
            before_id=cursor,
        )
        return {
            "items": [item.to_dict() for item in messages],
            "has_more": has_more,
        }

    def post_message(
        self,
        user: Any,
        room_id: str,
        content: str,
        *,
        parent_id: str | None = None,
        mentions: list[dict] | None = None,
    ) -> InteractionMessage:
        self._policy.require_access(user)
        actor = _actor(user)
        text = normalize_message_content(content)
        room = self.get_room(user, room_id)
        parent = self._parent_in_room(room.id, parent_id)
        created = self._repo.add_message(
            room_id=room.id,
            author_user_id=actor,
            content=text,
            parent_id=parent,
            mentions=normalize_mentions(mentions),
        )
        self._repo.mark_read(room_id=room.id, user_id=actor)
        confirmed = self._repo.get_message(created.id)
        if confirmed is None or confirmed.content != text or confirmed.author_user_id != actor:
            raise RuntimeError("OUTCOME_VERIFICATION_FAILED")
        if parent and confirmed.parent_id != parent:
            raise RuntimeError("OUTCOME_VERIFICATION_FAILED")
        return confirmed

    def edit_message(self, user: Any, room_id: str, message_id: str, content: str) -> InteractionMessage:
        actor = _actor(user)
        message = self._own_message(user, room_id, message_id, actor)
        if message.deleted_at is not None:
            raise ValueError("A mensagem foi removida.")
        text = normalize_message_content(content)
        updated = self._repo.update_message(message_id=message.id, content=text)
        if updated is None or updated.content != text or updated.edited_at is None:
            raise RuntimeError("OUTCOME_VERIFICATION_FAILED")
        return updated

    def delete_message(self, user: Any, room_id: str, message_id: str) -> InteractionMessage:
        actor = _actor(user)
        message = self._own_message(user, room_id, message_id, actor)
        if message.deleted_at is not None:
            return message
        deleted = self._repo.soft_delete_message(message.id)
        if deleted is None or deleted.deleted_at is None or deleted.to_dict()["content"] != "":
            raise RuntimeError("OUTCOME_VERIFICATION_FAILED")
        return deleted

    def toggle_reaction(self, user: Any, room_id: str, message_id: str, code: str) -> InteractionMessage:
        self._policy.require_access(user)
        actor = _actor(user)
        message = self._message_in_room(user, room_id, message_id)
        if message.deleted_at is not None:
            raise ValueError("A mensagem foi removida.")
        normalized = normalize_reaction_code(code)
        had = any(item.user_id == actor and item.code == normalized for item in message.reactions)
        self._repo.toggle_reaction(message_id=message.id, user_id=actor, code=normalized)
        confirmed = self._repo.get_message(message.id)
        has = confirmed is not None and any(
            item.user_id == actor and item.code == normalized for item in confirmed.reactions
        )
        if confirmed is None or has == had:
            raise RuntimeError("OUTCOME_VERIFICATION_FAILED")
        return confirmed

    def pin_message(self, user: Any, room_id: str, message_id: str) -> InteractionMessage:
        self._policy.require_access(user)
        actor = _actor(user)
        message = self._message_in_room(user, room_id, message_id)
        if message.deleted_at is not None:
            raise ValueError("A mensagem foi removida.")
        self._repo.pin_message(room_id=message.room_id, message_id=message.id, user_id=actor)
        confirmed = self._repo.get_message(message.id)
        if confirmed is None or not confirmed.pinned:
            raise RuntimeError("OUTCOME_VERIFICATION_FAILED")
        return confirmed

    def unpin_message(self, user: Any, room_id: str, message_id: str) -> InteractionMessage:
        self._policy.require_access(user)
        message = self._message_in_room(user, room_id, message_id)
        self._repo.unpin_message(room_id=message.room_id, message_id=message.id)
        confirmed = self._repo.get_message(message.id)
        if confirmed is None or confirmed.pinned:
            raise RuntimeError("OUTCOME_VERIFICATION_FAILED")
        return confirmed

    def mark_read(self, user: Any, room_id: str) -> None:
        self._policy.require_access(user)
        room = self.get_room(user, room_id)
        self._repo.mark_read(room_id=room.id, user_id=_actor(user))

    def list_attachments(self, user: Any, room_id: str) -> list[InteractionAttachment]:
        room = self.get_room(user, room_id)
        return self._repo.list_attachments(room.id)

    def add_attachment(
        self,
        user: Any,
        room_id: str,
        message_id: str,
        *,
        file_name: str,
        content: bytes,
        mime_type: str | None,
    ) -> InteractionAttachment:
        actor = _actor(user)
        message = self._own_message(user, room_id, message_id, actor)
        if message.deleted_at is not None:
            raise ValueError("A mensagem foi removida.")
        stored_name, safe_name = self._files().save(
            room_id=message.room_id,
            original_name=file_name,
            content=content,
            mime_type=mime_type,
        )
        created = self._repo.add_attachment(
            InteractionAttachment(
                id=str(uuid4()),
                message_id=message.id,
                room_id=message.room_id,
                file_name=safe_name,
                content_type=(mime_type or "").split(";")[0].strip().lower(),
                byte_size=len(content),
                uploaded_by_user_id=actor,
                created_at=None,
                stored_name=stored_name,
            )
        )
        confirmed = self._repo.get_attachment(created.id)
        if (
            confirmed is None
            or confirmed.message_id != message.id
            or confirmed.file_name != safe_name
            or confirmed.byte_size != len(content)
        ):
            raise RuntimeError("OUTCOME_VERIFICATION_FAILED")
        return confirmed

    def open_attachment(self, user: Any, room_id: str, attachment_id: str):
        self._policy.require_access(user)
        room = self.get_room(user, room_id)
        attachment = self._repo.get_attachment(normalize_uuid(attachment_id, label="O anexo"))
        if attachment is None or attachment.room_id != room.id:
            raise LookupError("Arquivo não encontrado.")
        path = self._files().resolve_file(room_id=room.id, stored_name=attachment.stored_name)
        return path, attachment.file_name, attachment.content_type

    def delete_attachment(self, user: Any, room_id: str, attachment_id: str) -> None:
        actor = _actor(user)
        self._policy.require_access(user)
        room = self.get_room(user, room_id)
        attachment = self._repo.get_attachment(normalize_uuid(attachment_id, label="O anexo"))
        if attachment is None or attachment.room_id != room.id:
            raise LookupError("Arquivo não encontrado.")
        if attachment.uploaded_by_user_id != actor:
            raise PermissionError("Só quem enviou pode remover este arquivo.")
        removed = self._repo.delete_attachment(attachment.id)
        if removed is None:
            raise RuntimeError("OUTCOME_VERIFICATION_FAILED")
        path = self._files().base_dir / room.id / removed.stored_name
        if path.is_file():
            path.unlink()

    def _files(self) -> InteractionAttachmentStorage:
        if self._storage is None:
            self._storage = InteractionAttachmentStorage()
        return self._storage

    def _parent_in_room(self, room_id: str, parent_id: str | None) -> str | None:
        if not parent_id:
            return None
        parent = self._repo.get_message(normalize_uuid(parent_id, label="A mensagem respondida"))
        if parent is None or parent.room_id != room_id or parent.deleted_at is not None:
            raise ValueError("A mensagem respondida não está nesta sala.")
        return parent.id

    def _message_in_room(self, user: Any, room_id: str, message_id: str) -> InteractionMessage:
        room = self.get_room(user, room_id)
        message = self._repo.get_message(normalize_uuid(message_id, label="A mensagem"))
        if message is None or message.room_id != room.id:
            raise LookupError("Mensagem não encontrada.")
        return message

    def _own_message(self, user: Any, room_id: str, message_id: str, actor: str) -> InteractionMessage:
        message = self._message_in_room(user, room_id, message_id)
        if message.author_user_id != actor:
            raise PermissionError("Só o autor pode alterar esta mensagem.")
        return message
