from __future__ import annotations

from typing import Protocol

from tm_app.domain.entities.interaction_room import (
    InteractionAttachment,
    InteractionMessage,
    InteractionRoom,
)


class InteractionRoomRepositoryPort(Protocol):
    def get_or_create(self, *, processo_id: str, created_by_user_id: str) -> InteractionRoom | None: ...

    def get(self, room_id: str) -> InteractionRoom | None: ...

    def list_rooms(
        self,
        *,
        viewer_user_id: str | None = None,
        inbox_filter: str = "all",
    ) -> list[InteractionRoom]: ...

    def list_messages(self, room_id: str, *, limit: int) -> tuple[list[InteractionMessage], bool]: ...

    def add_message(
        self,
        *,
        room_id: str,
        author_user_id: str,
        content: str,
        parent_id: str | None = None,
        mentions: tuple[tuple[str, str], ...] = (),
    ) -> InteractionMessage: ...

    def get_message(self, message_id: str) -> InteractionMessage | None: ...

    def update_message(self, *, message_id: str, content: str) -> InteractionMessage | None: ...

    def soft_delete_message(self, message_id: str) -> InteractionMessage | None: ...

    def toggle_reaction(self, *, message_id: str, user_id: str, code: str) -> None: ...

    def pin_message(self, *, room_id: str, message_id: str, user_id: str) -> None: ...

    def unpin_message(self, *, room_id: str, message_id: str) -> None: ...

    def mark_read(self, *, room_id: str, user_id: str) -> None: ...

    def add_attachment(self, attachment: InteractionAttachment) -> InteractionAttachment: ...

    def get_attachment(self, attachment_id: str) -> InteractionAttachment | None: ...

    def delete_attachment(self, attachment_id: str) -> InteractionAttachment | None: ...

    def list_attachments(self, room_id: str) -> list[InteractionAttachment]: ...
