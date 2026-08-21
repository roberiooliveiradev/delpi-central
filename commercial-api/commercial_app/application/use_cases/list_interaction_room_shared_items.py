from __future__ import annotations

from uuid import UUID

from commercial_app.domain.ports.attachment_repository_port import AttachmentRepositoryPort
from commercial_app.domain.ports.interaction_message_repository_port import (
    InteractionMessageRepositoryPort,
)
from commercial_app.domain.ports.interaction_room_repository_port import (
    InteractionRoomRepositoryPort,
)
from commercial_app.domain.services.interaction_room_access_service import (
    InteractionRoomAccessService,
)
from commercial_app.domain.services.interaction_room_content_service import (
    InteractionRoomContentService,
)
from commercial_app.domain.services.interaction_room_shared_items_service import (
    InteractionRoomSharedItemsService,
)

_ROOM_MESSAGE_OWNER = "room_message"
_DEFAULT_MESSAGE_SCAN = 200


class ListInteractionRoomSharedItemsUseCase:
    """Aggregate file attachments + http(s) links shared in a room."""

    def __init__(
        self,
        *,
        rooms: InteractionRoomRepositoryPort,
        messages: InteractionMessageRepositoryPort,
        attachments: AttachmentRepositoryPort,
    ) -> None:
        self._rooms = rooms
        self._messages = messages
        self._attachments = attachments
        self._access = InteractionRoomAccessService(rooms)

    def execute(
        self,
        *,
        room_id: UUID,
        actor_user_id: str,
        kind: str = "all",
        query: str | None = None,
        message_limit: int = _DEFAULT_MESSAGE_SCAN,
    ) -> list[dict]:
        actor = (actor_user_id or "").strip()
        if not actor:
            raise ValueError(InteractionRoomContentService.error("userIdRequired"))
        self._access.require_room_exists(room_id)

        limit = max(1, min(int(message_limit or _DEFAULT_MESSAGE_SCAN), 200))
        messages = list(
            self._messages.list_for_room(room_id=room_id, limit=limit, query=None)
        )
        attachments_by_message_id: dict[str, list] = {}
        kind_norm = (kind or "all").strip().lower()
        if kind_norm in {"all", "file", ""}:
            for message in messages:
                mid = str(message.id)
                rows = self._attachments.list_for_owner(
                    owner_type=_ROOM_MESSAGE_OWNER,
                    owner_id=mid,
                    limit=50,
                )
                if rows:
                    attachments_by_message_id[mid] = list(rows)

        return InteractionRoomSharedItemsService.assemble(
            messages=messages,
            attachments_by_message_id=attachments_by_message_id,
            kind=kind_norm or "all",
            query=query,
        )
