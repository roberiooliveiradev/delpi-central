from __future__ import annotations

from typing import Protocol

from tm_app.domain.entities.interaction_room import InteractionMessage, InteractionRoom


class InteractionRoomRepositoryPort(Protocol):
    def get_or_create(self, *, processo_id: str, created_by_user_id: str) -> InteractionRoom | None: ...

    def get(self, room_id: str) -> InteractionRoom | None: ...

    def list_rooms(self) -> list[InteractionRoom]: ...

    def list_messages(self, room_id: str, *, limit: int) -> tuple[list[InteractionMessage], bool]: ...

    def add_message(
        self,
        *,
        room_id: str,
        author_user_id: str,
        content: str,
    ) -> InteractionMessage: ...

    def get_message(self, message_id: str) -> InteractionMessage | None: ...
