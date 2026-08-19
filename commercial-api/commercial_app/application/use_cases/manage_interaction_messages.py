from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Mapping, Sequence
from uuid import UUID

from commercial_app.domain.entities.interaction_room import (
    MESSAGE_KINDS,
    InteractionMessage,
    InteractionPin,
)
from commercial_app.domain.ports.interaction_message_repository_port import (
    InteractionMessageRepositoryPort,
)
from commercial_app.domain.ports.interaction_room_repository_port import (
    InteractionRoomRepositoryPort,
)
from commercial_app.domain.services.interaction_mention_kinds_content_service import (
    InteractionMentionKindsContentService,
)
from commercial_app.domain.services.interaction_room_access_service import (
    InteractionRoomAccessService,
)
from commercial_app.domain.services.interaction_room_content_service import (
    InteractionRoomContentService,
)


@dataclass(frozen=True)
class PostInteractionMessageInput:
    room_id: UUID
    actor_user_id: str
    body_text: str
    message_kind: str = "text"
    parent_id: UUID | None = None
    mentions: Sequence[tuple[str, Mapping[str, object], str]] | None = None


class ManageInteractionMessagesUseCase:
    """CRUD de mensagens — acesso global via commercial.access na borda."""

    def __init__(
        self,
        *,
        rooms: InteractionRoomRepositoryPort,
        messages: InteractionMessageRepositoryPort,
    ) -> None:
        self._rooms = rooms
        self._messages = messages
        self._access = InteractionRoomAccessService(rooms)

    def _require_room_access(self, *, room_id: UUID, actor_user_id: str) -> None:
        actor = (actor_user_id or "").strip()
        if not actor:
            raise ValueError(InteractionRoomContentService.error("userIdRequired"))
        self._access.require_room_exists(room_id)

    def _validate_mentions(
        self,
        mentions: Sequence[tuple[str, Mapping[str, object], str]] | None,
    ) -> list[tuple[str, Mapping[str, object], str]]:
        cleaned: list[tuple[str, Mapping[str, object], str]] = []
        for kind, ref, label in mentions or ():
            mention_kind = str(kind or "").strip()
            mention_label = str(label or "").strip()
            if not mention_kind or not mention_label:
                continue
            if not InteractionMentionKindsContentService.is_known(mention_kind):
                raise ValueError(InteractionRoomContentService.error("kindUnknown"))
            cleaned.append((mention_kind, dict(ref), mention_label))
        return cleaned

    def list_messages(
        self,
        *,
        room_id: UUID,
        actor_user_id: str,
        limit: int = 50,
        before_created_at: datetime | None = None,
        before_id: UUID | None = None,
        query: str | None = None,
    ) -> Sequence[InteractionMessage]:
        self._require_room_access(room_id=room_id, actor_user_id=actor_user_id)
        return self._messages.list_for_room(
            room_id=room_id,
            limit=limit,
            before_created_at=before_created_at,
            before_id=before_id,
            query=query,
        )

    def post(self, request: PostInteractionMessageInput) -> InteractionMessage:
        self._require_room_access(
            room_id=request.room_id,
            actor_user_id=request.actor_user_id,
        )
        kind = (request.message_kind or "text").strip() or "text"
        if kind not in MESSAGE_KINDS:
            raise ValueError(InteractionRoomContentService.error("messageKindInvalid"))
        body = request.body_text if request.body_text is not None else ""
        if kind == "text" and not str(body).strip():
            raise ValueError(InteractionRoomContentService.error("bodyRequired"))
        if request.parent_id is not None:
            parent = self._messages.get_by_id(request.parent_id)
            if parent is None or parent.room_id != request.room_id:
                raise ValueError(InteractionRoomContentService.error("parentNotInRoom"))
        mentions = self._validate_mentions(request.mentions)
        return self._messages.create_message(
            room_id=request.room_id,
            author_user_id=request.actor_user_id.strip(),
            message_kind=kind,
            body_text=str(body),
            parent_id=request.parent_id,
            mentions=mentions,
        )

    def update(
        self,
        *,
        room_id: UUID,
        message_id: UUID,
        actor_user_id: str,
        body_text: str,
    ) -> InteractionMessage:
        self._require_room_access(room_id=room_id, actor_user_id=actor_user_id)
        message = self._messages.get_by_id(message_id)
        if (
            message is None
            or message.room_id != room_id
            or message.deleted_at is not None
        ):
            raise LookupError(InteractionRoomContentService.error("messageNotFound"))
        if (message.author_user_id or "").strip() != actor_user_id.strip():
            raise PermissionError(InteractionRoomContentService.error("notAuthor"))
        if not str(body_text or "").strip():
            raise ValueError(InteractionRoomContentService.error("bodyRequired"))
        updated = self._messages.update_body(
            message_id=message_id,
            body_text=body_text,
        )
        if updated is None:
            raise LookupError(InteractionRoomContentService.error("messageNotFound"))
        return updated

    def delete(
        self,
        *,
        room_id: UUID,
        message_id: UUID,
        actor_user_id: str,
    ) -> InteractionMessage:
        self._require_room_access(room_id=room_id, actor_user_id=actor_user_id)
        message = self._messages.get_by_id(message_id)
        if (
            message is None
            or message.room_id != room_id
            or message.deleted_at is not None
        ):
            raise LookupError(InteractionRoomContentService.error("messageNotFound"))
        if (message.author_user_id or "").strip() != actor_user_id.strip():
            raise PermissionError(InteractionRoomContentService.error("notAuthor"))
        deleted = self._messages.soft_delete(message_id=message_id)
        if deleted is None:
            raise LookupError(InteractionRoomContentService.error("messageNotFound"))
        return deleted

    def _require_message_in_room(
        self,
        *,
        room_id: UUID,
        message_id: UUID,
    ):
        message = self._messages.get_by_id(message_id)
        if (
            message is None
            or message.room_id != room_id
            or message.deleted_at is not None
        ):
            raise LookupError(InteractionRoomContentService.error("messageNotFound"))
        return message

    def set_reaction(
        self,
        *,
        room_id: UUID,
        message_id: UUID,
        actor_user_id: str,
        code: str,
    ):
        self._require_room_access(room_id=room_id, actor_user_id=actor_user_id)
        self._require_message_in_room(room_id=room_id, message_id=message_id)
        reaction_code = (code or "").strip()
        if not reaction_code:
            raise ValueError(InteractionRoomContentService.error("kindUnknown"))
        return self._messages.set_reaction(
            message_id=message_id,
            user_id=actor_user_id.strip(),
            code=reaction_code,
        )

    def clear_reaction(
        self,
        *,
        room_id: UUID,
        message_id: UUID,
        actor_user_id: str,
        code: str,
    ) -> None:
        self._require_room_access(room_id=room_id, actor_user_id=actor_user_id)
        self._require_message_in_room(room_id=room_id, message_id=message_id)
        reaction_code = (code or "").strip()
        if not reaction_code:
            raise ValueError(InteractionRoomContentService.error("kindUnknown"))
        self._messages.clear_reaction(
            message_id=message_id,
            user_id=actor_user_id.strip(),
            code=reaction_code,
        )

    def list_pins(
        self,
        *,
        room_id: UUID,
        actor_user_id: str,
    ) -> Sequence[InteractionPin]:
        self._require_room_access(room_id=room_id, actor_user_id=actor_user_id)
        return self._messages.list_pins(room_id)

    def pin(
        self,
        *,
        room_id: UUID,
        message_id: UUID,
        actor_user_id: str,
    ) -> InteractionPin:
        self._require_room_access(room_id=room_id, actor_user_id=actor_user_id)
        self._require_message_in_room(room_id=room_id, message_id=message_id)
        return self._messages.pin_message(
            room_id=room_id,
            message_id=message_id,
            pinned_by_user_id=actor_user_id.strip(),
        )

    def unpin(
        self,
        *,
        room_id: UUID,
        message_id: UUID,
        actor_user_id: str,
    ) -> bool:
        self._require_room_access(room_id=room_id, actor_user_id=actor_user_id)
        self._require_message_in_room(room_id=room_id, message_id=message_id)
        return self._messages.unpin_message(room_id=room_id, message_id=message_id)
