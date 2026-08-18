"""Publisher interno de mensagens system (OTD / etapa de processo) — sem HTTP."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from commercial_app.domain.entities.interaction_room import (
    MESSAGE_KINDS,
    InteractionMessage,
)
from commercial_app.domain.ports.interaction_message_repository_port import (
    InteractionMessageRepositoryPort,
)
from commercial_app.domain.ports.interaction_room_repository_port import (
    InteractionRoomRepositoryPort,
)
from commercial_app.domain.services.interaction_room_content_service import (
    InteractionRoomContentService,
)


@dataclass(frozen=True)
class PostSystemMessageInput:
    room_id: UUID
    event_kind: str
    body_text: str
    """Texto visível na linha system; event_kind valida allowlist JSON."""


class PostSystemMessageUseCase:
    """Publica message_kind=system para eventos internos (sem rota HTTP)."""

    def __init__(
        self,
        *,
        rooms: InteractionRoomRepositoryPort,
        messages: InteractionMessageRepositoryPort,
    ) -> None:
        self._rooms = rooms
        self._messages = messages

    def execute(self, request: PostSystemMessageInput) -> InteractionMessage:
        event_kind = (request.event_kind or "").strip()
        if not InteractionRoomContentService.is_allowed_system_event_kind(event_kind):
            raise ValueError(
                InteractionRoomContentService.error("systemEventKindInvalid")
            )
        body = str(request.body_text or "").strip()
        if not body:
            raise ValueError(InteractionRoomContentService.error("bodyRequired"))
        if self._rooms.get_by_id(request.room_id) is None:
            raise LookupError(InteractionRoomContentService.error("roomNotFound"))

        message_kind = InteractionRoomContentService.system_message_kind()
        if message_kind not in MESSAGE_KINDS:
            raise ValueError(InteractionRoomContentService.error("messageKindInvalid"))

        return self._messages.create_message(
            room_id=request.room_id,
            author_user_id=None,
            message_kind=message_kind,
            body_text=body,
        )
